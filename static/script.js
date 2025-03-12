// 🚀 Enter tuşu ile mesaj gönderme
function handleKeyPress(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
}

// 📩 Mesaj gönderme fonksiyonu
async function sendMessage() {
  let userInput = document.getElementById("user-input").value;
  if (!userInput.trim()) return;

  // Kullanıcı mesajını ekrana ekle
  addMessage(userInput, "user-message");

  // API'ye istek gönder
  let response = await fetch("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question: userInput }),
  });

  let data = await response.json();

  // Chatbot'un yanıtını ekrana ekle
  addMessage(data.answer, "bot-message");

  // Giriş kutusunu temizle
  document.getElementById("user-input").value = "";
}

// 🎨 Mesajları sohbet ekranına ekleme
function addMessage(text, className) {
  let chatBox = document.getElementById("chat-box");
  let messageDiv = document.createElement("div");
  messageDiv.className = "message " + className;
  messageDiv.innerText = text;
  chatBox.appendChild(messageDiv);

  // En yeni mesaja kaydır
  chatBox.scrollTop = chatBox.scrollHeight;
}
