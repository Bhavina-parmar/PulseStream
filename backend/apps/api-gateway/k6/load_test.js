import http from 'k6/http';
import { check, sleep} from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
    stages: [
        {duration: '30s', target:100},
        {duration: '1m', target: 100},
        {duration: '15s', target:0},
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
    },
};

export function setup(){
    const loginUrl = `${BASE_URL}/v1/auth/login`;
    const payload = JSON.stringify({
        email: __ENV.TEST_USER_EMAIL || 'user1@example.com',
        password: __ENV.TEST_USER_PASSWORD || 'User1123!',
    });
    const params = {
        headers: {
            'Content-Type': 'application/json',

        },
    };
    const res = http.post(loginUrl, payload, params);

    check(res, {
        'setup login succeeded': (r) => r.status === 200,
        'token present in response': (r) => r.json('access_token')!== undefined,
    });

    if (res.status !== 200){
        throw new Error(`Setup failed: Unable to log in. Status: ${res.status}, Body: ${res.body}`);
    }
    return {token: res.json('access_token')};
}

export default function (data) {
    const eventsUrl = `${BASE_URL}/v1/events/?skip=0&limit=10`;
    const params = {
        headers: {
            Authorization: `Bearer ${data.token}`,
            'Content-Type': 'application/json',
            'X-Forwarded-For': `10.0.${Math.floor(__VU / 256)}.${__VU % 256}`,
        },
    };
    const res = http.get(eventsUrl, params);
    check(res, {
        'status is 200':(r) => r.status === 200,
        'response is array': (r) => Array.isArray(r.json()),

    });
    sleep(1);
}