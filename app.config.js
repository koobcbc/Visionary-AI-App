import 'dotenv/config';

export default {
    expo: {
      extra: {
        GEMINI_API_KEY: process.env.GEMINI_API_KEY
      }
    }
  };