import { PostgrestClient } from "@supabase/postgrest-js";
import { createJWT, createJWTPayload } from "../jwt_utils";

const REST_URL = 'http://localhost:3003'
const jwt = createJWT(createJWTPayload());

export const getPostgrestClient = () => new PostgrestClient(REST_URL, {
    headers: {
        Authorization: `Bearer ${jwt}`,
        schema: 'dev',
    },
});