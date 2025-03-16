// Enter tuşu ile mesaj gönderme
function handleKeyPress(event) {
  if (event.key === "Enter") sendMessage();
}

// Mesaj gönderme fonksiyonu
async function sendMessage() {
  let userInput = document.getElementById("user-input").value;
  if (!userInput.trim()) return;

  addMessage(userInput, "user-message");

  let response = await fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: userInput }),
  });

  let data = await response.json();

  // Seslendirme butonuyla bot mesajı ekle
  addBotMessageWithSpeakBtn(data.answer);

  document.getElementById("user-input").value = "";
}

// Kullanıcı mesajlarını ekrana yazdırma
function addMessage(text, className) {
  let chatBox = document.getElementById("chat-box");
  let messageDiv = document.createElement("div");
  messageDiv.className = "message " + className;
  messageDiv.innerText = text;
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Bot mesajını seslendirme butonu ile ekleme
function addBotMessageWithSpeakBtn(text) {
  let chatBox = document.getElementById("chat-box");

  let messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";
  messageDiv.innerText = text;

  // Seslendirme butonu oluştur
  let speakBtn = document.createElement("button");
  speakBtn.className = "speak-btn";
  speakBtn.innerText = "🔊";

  // Seslendirme durumunu tut
  let isSpeaking = false;
  let utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "tr-TR";

  speakBtn.onclick = () => {
    if (!isSpeaking) {
      // Eğer konuşmuyorsa başlat
      speechSynthesis.cancel(); // önceki varsa iptal et
      speechSynthesis.speak(utterance);
      isSpeaking = true;
    } else if (speechSynthesis.speaking) {
      // Şu an konuşuyorsa durdur
      speechSynthesis.cancel();
      isSpeaking = false;
    } else {
      // Üçüncü basış ve sonrası: yeniden başlat
      speechSynthesis.cancel();
      speechSynthesis.speak(utterance);
      isSpeaking = true;
    }
  };

  // Konuşma bittiğinde isSpeaking durumunu sıfırla
  utterance.onend = () => {
    isSpeaking = false;
  };

  messageDiv.appendChild(speakBtn);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// 🔈 Metni seslendirme fonksiyonu
function speak(text) {
  const speech = new SpeechSynthesisUtterance(text);
  speech.lang = "tr-TR";
  speechSynthesis.speak(speech);
}

// 🎙️ Speech-to-text mikrofon özelliği
document.addEventListener("DOMContentLoaded", () => {
  const voiceBtn = document.getElementById("voice-btn");
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = "tr-TR";

    voiceBtn.onclick = () => {
      recognition.start();
      voiceBtn.innerText = "🎙️ Dinleniyor...";
    };

    recognition.onresult = (event) => {
      const spokenText = event.results[0][0].transcript;
      document.getElementById("user-input").value = spokenText;
      sendMessage();
    };

    recognition.onend = () => {
      voiceBtn.innerText = "🎤";
    };

    recognition.onerror = (event) => {
      console.error("Ses Tanıma Hatası:", event.error);
      voiceBtn.innerText = "🎤";
    };
  } else {
    voiceBtn.disabled = true;
    alert("Tarayıcınız ses tanımayı desteklemiyor!");
  }
});
