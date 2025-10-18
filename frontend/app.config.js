import 'dotenv/config';
import appJson from './app.json';


export default {
    ...appJson,
    expo: {
      extra: {
        GEMINI_API_KEY: process.env.GEMINI_API_KEY,
      }
    }
  };