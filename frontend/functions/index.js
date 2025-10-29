const functions = require("firebase-functions");
const admin = require("firebase-admin");
const {BigQuery} = require("@google-cloud/bigquery");
const {GoogleGenerativeAI} = require("@google/generative-ai");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");
const { onCall } = require("firebase-functions/v2/https");
const axios = require("axios");

admin.initializeApp();

const bq = new BigQuery();
const datasetId = "chat_analysis";
const tableId = "messages";
console.log("functions keys:", Object.keys(functions));

// Temporarily comment out to avoid deployment conflict
// exports.streamChatToBigQuery = onDocumentCreated("chats/{chatId}", async (event) => {
//   const data = event.data?.fields;
//
//   const row = {
//     chatId: event.params.chatId,
//     userId: data?.userId?.stringValue || null,
//     text: data?.text?.stringValue || null,
//     timestamp: data.timestamp.toDate().toISOString(),
//     imageUrl: data?.imageUrl?.stringValue || null,
//   };
//
//   try {
//     await bq.dataset(datasetId).table(tableId).insert([row]);
//     console.log("Inserted:", row);
//   } catch (err) {
//     console.error("BigQuery insert error:", err);
//   }
// });

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

exports.fetchDoctors = onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
        "unauthenticated",
        "Authentication required.",
    );
  }

  const { specialty, zipCode, state = "IL" } = data;

  if (!specialty || typeof specialty !== "string") {
    throw new functions.https.HttpsError(
        "invalid-argument",
        "Specialty must be a non-empty string.",
    );
  }

  try {
    let url = `https://npiregistry.cms.hhs.gov/api/?version=2.1&taxonomy_description=${encodeURIComponent(specialty)}&limit=20`;
    
    if (zipCode) {
      url += `&postal_code=${zipCode}`;
    } else {
      url += `&state=${state}`;
    }

    const response = await axios.get(url);
    const json = response.data;

    if (!json.results) {
      throw new Error("No results found");
    }

    const doctors = json.results.map((doc) => {
      const basic = doc.basic || {};
      const address = doc.addresses?.[0] || {};
      const name = `${basic.first_name || ""} ${basic.last_name || ""}`.trim();
      const doctorSpecialty = doc.taxonomies?.[0]?.desc || "N/A";
      const fullAddress = `${address.address_1 || ""} ${address.city || ""}, ${address.state || ""} ${address.postal_code || ""}`;
      const mapQuery = `${address.address_1 || ""}, ${address.city || ""}, ${address.state || ""}`;

      return {
        name: name || basic.organization_name || "Unknown",
        specialty: doctorSpecialty,
        address: fullAddress,
        mapQuery,
      };
    });

    return { doctors };
  } catch (err) {
    console.error("NPI API error:", err);
    throw new functions.https.HttpsError(
        "internal",
        "Error fetching doctors from NPI Registry.",
    );
  }
});
