const ApiEndpoint = "/api/";

// GET request with query params
export async function GetRequestWithParams(url, params) {
    const response = await fetch(`${url}?${params}`, {
        method: 'GET'
    });

    let result;
    try {
        result = await response.json();
    } catch (err) {
        result = { error: "Invalid response format from server" };
    }

    return { response, result };
}

// POST request with JSON body
export async function PostRequestWithBody(url, params) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    });

    let result;
    try {
        result = await response.json();
    } catch (err) {
        result = { error: "Invalid response format from server" };
    }

    return { response, result };
}

// USER API

export async function Login(Username, Password) {
    return await GetRequestWithParams(ApiEndpoint + "user/login", new URLSearchParams({
        username: Username,
        password: Password
    }));
}

export async function Signup(Username, Password) {
    return await PostRequestWithBody(ApiEndpoint + "user/signup", {
        username: Username,
        password: Password
    });
}

// FEED API
export async function PostFeed(Token) {
    return GetRequestWithParams(ApiEndpoint  + "feed/post", new URLSearchParams({
        token:Token
    }));
}

export async function ThreadFeed(Token) {
    return GetRequestWithParams(ApiEndpoint  + "feed/thread", new URLSearchParams({
        token:Token
    }));
}