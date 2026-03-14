const products = [
  { name: "Aurora Sneakers", price: 129.0, tag: "Best Seller" },
  { name: "Metro Sling Bag", price: 89.0, tag: "New" },
  { name: "Cloud Knit Hoodie", price: 74.0, tag: "Limited" },
  { name: "Pulse Smart Watch", price: 199.0, tag: "Hot Deal" },
  { name: "Luna Wireless Earbuds", price: 159.0, tag: "Popular" },
  { name: "Nova Water Bottle", price: 32.0, tag: "Eco Pick" },
];

const productGrid = document.getElementById("product-grid");
const cartList = document.getElementById("cart-list");
const cartTotal = document.getElementById("cart-total");
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const threadIdEl = document.getElementById("thread-id");
const newChatBtn = document.getElementById("new-chat");
const clearUiBtn = document.getElementById("clear-ui");

const cart = [];
let threadId = localStorage.getItem("neomall_thread_id") || `thread-${crypto.randomUUID()}`;
let chatHistory = [];

function persistThread() {
  localStorage.setItem("neomall_thread_id", threadId);
  threadIdEl.textContent = threadId;
}

function addMessage(role, content, source = null) {
  chatHistory.push({ role, content, source });
  const wrap = document.createElement("div");
  wrap.className = `msg-wrap ${role}`;
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = content;
  wrap.appendChild(div);
  if (source) {
    const badge = document.createElement("span");
    badge.className = "msg-source";
    badge.textContent = `[${source}]`;
    wrap.appendChild(badge);
  }
  chatLog.appendChild(wrap);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function clearMessages() {
  chatHistory = [];
  chatLog.innerHTML = "";
}

function renderCart() {
  cartList.innerHTML = "";
  let total = 0;

  for (const item of cart) {
    total += item.price;
    const li = document.createElement("li");
    li.textContent = `${item.name} ($${item.price.toFixed(2)})`;
    cartList.appendChild(li);
  }

  cartTotal.textContent = `Total: $${total.toFixed(2)}`;
}

function renderProducts() {
  productGrid.innerHTML = "";

  products.forEach((product) => {
    const card = document.createElement("article");
    card.className = "product-card";
    card.innerHTML = `
      <span class="tag">${product.tag}</span>
      <h3>${product.name}</h3>
      <p>$${product.price.toFixed(2)}</p>
      <button>Add to Cart</button>
    `;

    const btn = card.querySelector("button");
    btn.addEventListener("click", () => {
      cart.push(product);
      renderCart();
    });

    productGrid.appendChild(card);
  });
}

async function sendChat(message) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Request failed");
  }

  return response.json();
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  chatInput.value = "";

  try {
    const data = await sendChat(message);
    threadId = data.thread_id || threadId;
    persistThread();
    addMessage("assistant", data.reply || "(응답 없음)", data.source ?? null);
  } catch (error) {
    addMessage("assistant", `Error: ${error.message}`);
  }
});

newChatBtn.addEventListener("click", () => {
  threadId = `thread-${crypto.randomUUID()}`;
  persistThread();
  clearMessages();
});

clearUiBtn.addEventListener("click", () => {
  clearMessages();
});

persistThread();
renderProducts();
renderCart();
addMessage("assistant", "안녕하세요. 주문/환불/결제 관련 문의를 도와드릴게요.");
