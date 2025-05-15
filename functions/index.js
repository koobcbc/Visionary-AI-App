const functions = require("firebase-functions");
const admin = require("firebase-admin");
const {BigQuery} = require("@google-cloud/bigquery");
const {GoogleGenerativeAI} = require("@google/generative-ai");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");
const { onCall } = require("firebase-functions/v2/https");

admin.initializeApp();

const bq = new BigQuery();
const datasetId = "chat_analysis";
const tableId = "messages";
console.log("functions keys:", Object.keys(functions));

exports.streamChatToBigQuery = onDocumentCreated("chats/{chatId}", async (event) => {
  const data = event.data?.fields;

  const row = {
    chatId: event.params.chatId,
    userId: data?.userId?.stringValue || null,
    text: data?.text?.stringValue || null,
    timestamp: data.timestamp.toDate().toISOString(),
    imageUrl: data?.imageUrl?.stringValue || null,
  };

  try {
    await bq.dataset(datasetId).table(tableId).insert([row]);
    console.log("Inserted:", row);
  } catch (err) {
    console.error("BigQuery insert error:", err);
  }
});

exports.generateFromGemini = onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
        "unauthenticated",
        "Authentication required.",
    );
  }

  const userPrompt = data.prompt;

  if (!userPrompt || typeof userPrompt !== "string") {
    throw new functions.https.HttpsError(
        "invalid-argument",
        "Prompt must be a non-empty string.",
    );
  }

  try {
    const API_KEY = process.env.GEMINI_KEY;

    if (!API_KEY) {
      throw new Error("Missing Gemini API key in environment config.");
    }

    const gemini = new GoogleGenerativeAI(API_KEY);
    const model = gemini.getGenerativeModel({model: "gemini-pro"});

    const result = await model.generateContent(userPrompt);
    const response = result.response;
    const text = await response.text();

    return {text};
  } catch (err) {
    console.error("Gemini error:", err);
    throw new functions.https.HttpsError(
        "internal",
        "Error generating response from Gemini.",
    );
  }
});
