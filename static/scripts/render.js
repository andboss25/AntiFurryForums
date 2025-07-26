import { LikePost, ViewThread } from "/static/scripts/requests.js";

export function escapeHTML(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, function (char) {
    const escapeChars = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    };
    return escapeChars[char];
  });
}

let lastPostId = null; // Track for pagination

export async function LoadPosts(container, message, response, result, append = false) {
  if (!append) {
    container.innerHTML = "";
    message.innerText = "";
    lastPostId = null;
  }

  try {
    if (response.ok && result.Posts && result.Posts.length > 0) {
      for (const post of result.Posts) {
        const div = document.createElement("div");
        let imageattach = "";

        if (post.image_attachment) {
          const isImg = /\.(png|jpeg|gif)$/i.test(post.image_attachment);
          const isVid = /\.mp4$/i.test(post.image_attachment);

          if (isImg) {
            imageattach = `<img src="${post.image_attachment}" alt="Image failed to load" id="postimg"/>`;
          } else if (isVid) {
            imageattach = `<video width="320" height="240" controls><source src="${post.image_attachment}" type="video/mp4"/></video>`;
          }
        }

        div.className = "post_card";
        const isLiked = post.liked;
        const likeCount = post.likes;

        div.innerHTML = `
          <div class="post_title"><a href="/view/post/${post.id}" id="title_text">${escapeHTML(post.title)}</a></div>
          <div class="post_meta">
            posted on thread <a id="owner_link" href="/view/threads/${post.post_identifier}">/${post.post_identifier}/</a>
            by <a id="owner_link" href="/view/users/${post.owner_username}">@${post.owner_username}</a>
            ${new Date(post.timestamp).toLocaleString()}
          </div>
          <div class="post_content">${escapeHTML(post.content)}</div>
          ${imageattach}
          <div class="post_meta">
            <button class="like_btn" data-id="${post.id}" data-liked="${isLiked}">${isLiked ? "Unlike" : "Like"}</button>
            <a id="repbtn" href="/report/${post.id}">report this post</a>
            <span class="like_count" id="like_count_${post.id}">${likeCount} like${likeCount !== 1 ? "s" : ""}</span>
          </div>
        `;

        container.appendChild(div);
        lastPostId = post.id; // Update last seen ID
      }

      document.querySelectorAll(".like_btn").forEach(button => {
        button.onclick = async () => {
          const postId = button.getAttribute("data-id");
          const liked = button.getAttribute("data-liked") === "true";
          const action = liked ? "unlike" : "like";

          try {
            const { response: res } = await LikePost(postId, action);
            if (res.ok) {
              button.setAttribute("data-liked", (!liked).toString());
              button.textContent = liked ? "Like" : "Unlike";

              const countSpan = document.getElementById(`like_count_${postId}`);
              let currentCount = parseInt(countSpan.innerText) || 0;
              currentCount = liked ? currentCount - 1 : currentCount + 1;
              countSpan.innerText = `${currentCount} like${currentCount !== 1 ? "s" : ""}`;
            } else {
              location.reload();
            }
          } catch (err) {
            console.error("Like error:", err);
            alert("An error occurred while liking the post.");
          }
        };
      });
    } else {
      message.innerText = result.Error || "No more posts available.";
    }
  } catch (err) {
    console.error("Feed fetch error:", err);
    message.innerText = "An error occurred while loading your feed.";
  }
}

export async function LoadThreads(container, response, result) {
  if (!container) {
    console.error("Threads container not found.");
    return;
  }

  container.innerHTML = "";

  if (response.ok && result.Threads && result.Threads.length > 0) {
    for (const thread of result.Threads) {
      const div = document.createElement("div");
      div.className = "thread_card";
      div.innerHTML = `
        <div>
          <h3 class="thread_name">Thread:</h3>${escapeHTML(thread.name)} - 
          <a href="/view/threads/${escapeHTML(thread.identifier)}" id="title_text">/${escapeHTML(thread.identifier)}/</a>
        </div>
      `;
      container.appendChild(div);
    }
  } else {
    container.innerHTML = "<p>No recommended threads found.</p>";
  }
}

export async function RenderThreadView(identifier, response, result) {
  const message = document.getElementById("message");
  const subBtn = document.getElementById("sub_to_thread");
  const postContainer = document.getElementById("posts_container");

  if (response.ok && result.Threads && result.Threads.length > 0) {
    const thread = result.Threads[0];

    document.getElementById("identifier").innerText = "/" + thread.identifier;
    document.getElementById("owner").innerHTML = `owned by <a id="owner_link" href="/view/users/${thread.owner_username}">@${thread.owner_username}</a>`;
    document.getElementById("name").innerText = thread.name;
    document.getElementById("sub_count").innerText = "subscriber count: " + thread.subscribed_count;
    document.getElementById("description").innerText = '"' + (thread.description?.trim() || "No description set for this thread.") + '"';

    subBtn.innerText = thread.subscribed ? "Unsubscribe from thread" : "Subscribe to thread";
    subBtn.onclick = () => SubscribeThread(identifier);

    const postResponse = await fetch('/api/post/view?' + new URLSearchParams({
      post_identifier: identifier,
      search: false
    }), { credentials: 'include' });

    const postResult = await postResponse.json();
    await LoadPosts(postContainer, message, postResponse, postResult);
  } else {
    document.getElementById("basic_info").style.display = "none";
    document.getElementById("basic_info_2").style.display = "none";
    message.innerText = "Thread not found!";
    document.getElementById("mkthread").style.display = "block";
    message.style.display = "block";
  }
}

export async function SubscribeThread(identifier) {
  const button = document.getElementById("sub_to_thread");
  const action = button.innerText.includes("Unsubscribe") ? "unsubscribe" : "subscribe";

  try {
    const response = await fetch('/api/thread/subscribe', {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier,
        action
      })
    });

    const result = await response.json();

    if (response.ok) {
      const { response: threadResponse, result: threadResult } = await ViewThread(identifier, false);
      await RenderThreadView(identifier, threadResponse, threadResult);
    } else {
      alert(result.Error || "Subscription action failed.");
    }
  } catch (error) {
    console.error("Subscription error:", error);
    alert("An error occurred while trying to subscribe.");
  }
}
