// Global değişken: aktif oturum ID'si
let currentSessionId = null;

// Sayfa yüklendiğinde mevcut oturumları getir ve Yeni Chat butonunu dinle
window.addEventListener("load", () => {
  fetchSessions();
  // Yeni Chat butonuna tıklama olayını ekle
  document
    .getElementById("new-chat-btn")
    .addEventListener("click", function () {
      currentSessionId = null; // Aktif oturum sıfırlanır
      document.getElementById("chat-box").innerHTML = ""; // Chat alanı temizlenir
      document.getElementById("user-input").value = ""; // Giriş alanı temizlenir
    });
});

// 🚀 Enter tuşu ile mesaj gönderme
function handleKeyPress(event) {
  if (event.key === "Enter") sendMessage();
}

// 📩 Mesaj gönderme fonksiyonu (SESSION entegrasyonlu)
async function sendMessage(userInput = null) {
  let inputField = document.getElementById("user-input");
  let userMessage = userInput || inputField.value;

  if (!userMessage.trim()) return;

  // Kullanıcı mesajını UI'ya ekle
  addMessage(userMessage, "user-message");

  // Aktif oturum kontrolü: Eğer oturum yoksa yeni oturum oluştur, varsa mesaj ekle
  let url = "";
  if (!currentSessionId) {
    url = "/sessions";
  } else {
    url = `/sessions/${currentSessionId}/messages`;
  }

  try {
    let response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userMessage }),
    });

    let data = await response.json();

    // Yeni oturum oluşturulmuşsa aktif oturum ID'sini al
    if (!currentSessionId && data.id) {
      currentSessionId = data.id;
    }

    // API'den gelen bot cevabı; ya direkt data.answer ya da messages listesinin son elemanı
    let botAnswer =
      data.answer ||
      (data.messages ? data.messages[data.messages.length - 1].content : "");
    addBotMessageWithSpeakBtn(botAnswer);

    // Oturum listesini güncelle
    fetchSessions();
  } catch (error) {
    console.error("Error sending message:", error);
  }

  inputField.value = "";
}

// 🎨 Kullanıcı mesajlarını ekrana yazdırma
function addMessage(text, className) {
  let chatBox = document.getElementById("chat-box");
  let messageDiv = document.createElement("div");
  messageDiv.className = "message " + className;
  messageDiv.innerText = text;
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// 🤖 Bot mesajını seslendirme butonu ile ekleme
function addBotMessageWithSpeakBtn(text) {
  let chatBox = document.getElementById("chat-box");

  let messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";
  messageDiv.innerText = text;

  let speakBtn = document.createElement("button");
  speakBtn.className = "speak-btn";
  speakBtn.innerText = "🔊";

  let utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "tr-TR";

  let isSpeaking = false; // Konuşma durumu
  let isPaused = false; // Durdurulmuş mu kontrolü

  speakBtn.onclick = () => {
    if (!isSpeaking) {
      // Eğer konuşma başlamadıysa, başlat
      speechSynthesis.cancel();
      speechSynthesis.speak(utterance);
      isSpeaking = true;
      isPaused = false;
    } else if (!isPaused) {
      // Eğer konuşma devam ediyorsa, durdur
      speechSynthesis.cancel();
      isPaused = true;
    } else {
      // Eğer konuşma durmuşsa, en baştan başlat
      speechSynthesis.cancel();
      speechSynthesis.speak(utterance);
      isPaused = false;
    }
  };

  messageDiv.appendChild(speakBtn);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// --- YENİ OTURUM YÖNETİMİ KISMI ---

// Mevcut tüm oturumları GET /sessions endpoint'i ile getirir ve sol panelde listeler
function fetchSessions() {
  fetch("/sessions")
    .then((response) => response.json())
    .then((data) => {
      renderSessionList(data);
    })
    .catch((error) => console.error("Error fetching sessions:", error));
}

// Sol panelde oturum listesini oluşturur
function renderSessionList(sessions) {
  let container = document.getElementById("chat-history");
  container.innerHTML = ""; // Önce temizle
  sessions.forEach((session) => {
    let sessionDiv = document.createElement("div");
    sessionDiv.className = "session-item";

    let titleSpan = document.createElement("span");
    titleSpan.textContent = session.title;

    // Çöp kutusu ikonu ekle
    let deleteBtn = document.createElement("button");
    deleteBtn.innerHTML = '<span style="color:red;">🗑️</span>';
    deleteBtn.className = "delete-btn";
    deleteBtn.onclick = (e) => {
      e.stopPropagation(); // sessionDiv onclick tetiklenmesini engelle
      deleteSession(session.id);
    };

    // DÜZENLE butonu ekle (✏️)
    let renameBtn = document.createElement("button");
    renameBtn.innerHTML = '<span style="color:yellow;">✏️</span>';
    renameBtn.className = "rename-btn";
    renameBtn.onclick = (e) => {
      e.stopPropagation();
      showRenameModal(session.id, session.title);
    };

    // Oturuma tıklanınca yükle
    sessionDiv.onclick = () => {
      loadSession(session.id);
    };

    // Eklemeleri DOM'a sırayla koy
    sessionDiv.appendChild(titleSpan);
    sessionDiv.appendChild(renameBtn);
    sessionDiv.appendChild(deleteBtn);
    container.appendChild(sessionDiv);
  });
}

// Belirli bir oturumu GET /sessions/{session_id} endpoint'iyle getirip, chat kutusuna yükler
function loadSession(sessionId) {
  fetch(`/sessions/${sessionId}`)
    .then((response) => response.json())
    .then((data) => {
      currentSessionId = data.id;
      renderSessionMessages(data.messages);
    })
    .catch((error) => console.error("Error loading session:", error));
}

// Oturum içindeki mesajları chat kutusuna yazar
function renderSessionMessages(messages) {
  let chatBox = document.getElementById("chat-box");
  chatBox.innerHTML = ""; // Önce temizle
  messages.forEach((msg) => {
    let className = msg.role === "user" ? "user-message" : "bot-message";
    addMessage(msg.content, className);
  });
}

// --- SON YENİ OTURUM YÖNETİMİ KISMI ---

// 🎙️ Sürekli dinleme ve "Asistan" tetiklemesi
document.addEventListener("DOMContentLoaded", () => {
  const voiceBtn = document.getElementById("voice-btn");
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    alert("Tarayıcınız ses tanımayı desteklemiyor!");
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "tr-TR";
  recognition.continuous = true;
  recognition.interimResults = false;

  let isListeningForQuery = false;

  recognition.onresult = (event) => {
    const transcript =
      event.results[event.results.length - 1][0].transcript.toLowerCase();
    console.log("🎤 Algılanan kelime:", transcript);

    if (transcript.includes("asistan") && !isListeningForQuery) {
      console.log(
        "✨ 'Asistan' kelimesi algılandı. Şimdi tam dinleme moduna geçiyoruz..."
      );
      isListeningForQuery = true;
      recognition.stop();
      setTimeout(listenForQuery, 500); // Küçük bir gecikme ekleyerek ikinci tanımanın düzgün çalışmasını sağlıyoruz
    }
  };

  recognition.onerror = (event) => {
    console.error("⚠️ Ses Tanıma Hatası:", event.error);
  };

  recognition.start();

  function listenForQuery() {
    const queryRecognition = new SpeechRecognition();
    queryRecognition.lang = "tr-TR";
    queryRecognition.continuous = false;
    queryRecognition.interimResults = false;

    queryRecognition.start();
    console.log("🎤 Kullanıcının sorusu dinleniyor...");

    queryRecognition.onresult = (event) => {
      const userQuery = event.results[0][0].transcript;
      console.log("📨 Algılanan soru:", userQuery);
      sendMessage(userQuery);
      isListeningForQuery = false;
      setTimeout(() => recognition.start(), 1000); // Tekrar \"Asistan\" dinlemesi başlat
    };

    queryRecognition.onerror = (event) => {
      console.error("⚠️ Soru Tanıma Hatası:", event.error);
      isListeningForQuery = false;
      setTimeout(() => recognition.start(), 1000);
    };
  }

  voiceBtn.onclick = () => {
    listenForQuery();
  };
});

// Oturum silme işlemi (API isteği ve yenileme)
function deleteSession(sessionId) {
  showDeleteConfirmation(sessionId);
}

// Onay Modalı (Silme)
function showDeleteConfirmation(sessionId) {
  const modal = document.getElementById("confirm-modal");
  modal.style.display = "block";

  const yesBtnOld = document.getElementById("confirm-yes");
  const noBtnOld = document.getElementById("confirm-no");

  let yesBtn = yesBtnOld.cloneNode(true);
  yesBtnOld.parentNode.replaceChild(yesBtn, yesBtnOld);

  let noBtn = noBtnOld.cloneNode(true);
  noBtnOld.parentNode.replaceChild(noBtn, noBtnOld);

  yesBtn.onclick = function () {
    fetch(`/sessions/${sessionId}`, { method: "DELETE" })
      .then((response) => {
        if (response.ok) {
          fetchSessions();
          document.getElementById("chat-box").innerHTML = "";
          currentSessionId = null;
        } else {
          alert("Silme işlemi başarısız oldu.");
        }
      })
      .catch((error) => console.error("Error deleting session:", error));
    modal.style.display = "none";
  };

  noBtn.onclick = function () {
    modal.style.display = "none";
  };
}

// YENİ EKLENEN KOD: Oturum Adını Değiştirme (Modal)
function showRenameModal(sessionId, currentTitle) {
  const renameModal = document.getElementById("rename-modal");
  renameModal.style.display = "block";

  let renameInput = document.getElementById("rename-input");
  renameInput.value = currentTitle || "";

  let yesBtnOld = document.getElementById("rename-yes");
  let noBtnOld = document.getElementById("rename-no");

  let yesBtn = yesBtnOld.cloneNode(true);
  yesBtnOld.parentNode.replaceChild(yesBtn, yesBtnOld);

  let noBtn = noBtnOld.cloneNode(true);
  noBtnOld.parentNode.replaceChild(noBtn, noBtnOld);

  yesBtn.onclick = function () {
    let newTitle = renameInput.value.trim();
    if (!newTitle) {
      renameModal.style.display = "none";
      return;
    }
    fetch(`/sessions/${sessionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle }),
    })
      .then((response) => {
        if (!response.ok) {
          alert("Oturum adı güncellenemedi!");
        }
        return response.json();
      })
      .then((data) => {
        if (data.newTitle) {
          fetchSessions();
        }
      })
      .catch((error) => console.error("Error renaming session:", error));
    renameModal.style.display = "none";
  };

  noBtn.onclick = function () {
    renameModal.style.display = "none";
  };
}
