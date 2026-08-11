import http from 'k6/http';
import { check, sleep} from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
    stages: [
        { duration: '30s', target: 50},
        { duration: '1m', target: 50},
        {duration: '15s', target: 0},
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
        'setup login succeeded':(r)=> r.status ===200,
        'token present in response': (r) => r.json('access_token') !==undefined,
    });
    if(res.status!==200){
        throw new Error(`Setup failed: Unablle to log in. Status: ${res.status}, Body: ${res.body}`);

    }
    return {token:res.json('access_token')};
}

function getIpForVu(){
    return `10.0.${Math.floor(__VU / 256)}.${__VU % 256}`;
}

export default function(data){
    const ingestionUrl = `${BASE_URL}/v1/events/`;
    const vuIp=getIpForVu();
    const eventPayload = JSON.stringify({
        event_type: 'USER_LOGIN',
        source: 'web-client',
        payload:{
            ip: vuIp,
            device: 'desktop',
        },
    });

    const params = {
        headers: {
            'Authorization': `Bearer ${data.token}`,
            'Content-Type': 'application/json',
            'X-Forwarded-For': vuIp,
        },
    };
    

    const res = http.post(ingestionUrl, eventPayload, params);
    check(res,{
        'status is 201 or 202':(r)=>r.status === 202,
        'response contains event id': (r) => r.json('id') !== undefined,
    });
    sleep(1);
}