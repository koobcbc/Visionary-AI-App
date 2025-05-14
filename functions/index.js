const functions = require("firebase-functions");
const { BigQuery } = require("@google-cloud/bigquery");
const admin = require("firebase-admin");

admin.initializeApp();
const bq = new BigQuery();
const datasetId = "chat_analysis";
const tableId = "messages";

exports.streamChatToBigQuery = functions.firestore
  .document("chats/{chatId}")
  .onCreate(async (snap, context) => {
    const data = snap.data();
    const row = {
      chatId: context.params.chatId,
      userId: data.userId || null,
      text: data.text || null,
      timestamp: data.timestamp.toDate().toISOString(),
      imageUrl: data.imageUrl || null
    };

    try {
      await bq.dataset(datasetId).table(tableId).insert([row]);
      console.log(`Inserted: ${JSON.stringify(row)}`);
    } catch (err) {
      console.error("BigQuery insert error:", err);
    }
  });