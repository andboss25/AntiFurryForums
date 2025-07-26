const ApiEndpoint = "/api/";

// GET request with query params
export async function GetRequestWithParams(url, params) {
    const response = await fetch(`${url}?${params}`, {
        method: 'GET',
        credentials: 'include'  // <-- Include cookies!
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
        credentials: 'include',  // <-- Include cookies!
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

// THREAD API

export async function ViewThread(identifier, search) {
    return GetRequestWithParams(ApiEndpoint + "thread/view", new URLSearchParams({
        thread_identifier: identifier,
        search: search
    }));
}

// POST API

export async function LikePost(id, action) {
    return PostRequestWithBody(ApiEndpoint + "post/like", {
        id: id,
        action: action
    });
}

// FEED API

export async function PostFeed(params = "") {
    return GetRequestWithParams(ApiEndpoint + "feed/post", params);
}

export async function ThreadFeed() {
    return GetRequestWithParams(ApiEndpoint + "feed/thread", "");
}
