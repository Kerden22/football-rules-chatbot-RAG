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

// Dosya inputunu tetikleyen fonksiyon
function triggerFileInput() {
  document.getElementById("document-input").click();
}

// Dosya yükleme fonksiyonu
async function uploadDocument() {
  const fileInput = document.getElementById("document-input");
  if (!fileInput.files.length) {
    // Dosya seçilmediyse hata modali göster
    showErrorModal("Lütfen bir dosya seçin!");
    return;
  }
  const file = fileInput.files[0];
  console.log("Seçilen dosya tipi:", file.type);

  const allowedTypes = [
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];
  if (!allowedTypes.includes(file.type)) {
    showErrorModal(
      "Lütfen yalnızca PDF, TXT veya DOCX formatındaki dosyaları yükleyin."
    );
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    let response = await fetch("/upload-document", {
      method: "POST",
      body: formData,
    });
    let data = await response.json();
    if (data.session_id) {
      currentSessionId = data.session_id;
      // Başarı mesajını chat'e sistem mesajı olarak ekle
      addMessage(
        "Belge başarıyla yüklendi ve işlendi. Artık soru sorabilirsiniz.",
        "system-message"
      );
      fetchSessions();
    } else {
      showErrorModal("Belge işleme sırasında bir sorun oluştu.");
    }
  } catch (error) {
    console.error("Dosya yükleme hatası:", error);
    showErrorModal("Dosya yükleme sırasında bir hata oluştu.");
  }
}

// Reset doküman fonksiyonu
async function resetDocument() {
  if (!currentSessionId) {
    showErrorModal("Reset işlemi için seçili bir oturum bulunmuyor.");
    return;
  }
  try {
    let response = await fetch(`/sessions/${currentSessionId}/reset-document`, {
      method: "POST",
    });
    let data = await response.json();
    if (data.status === "document reset") {
      // Başarı durumunda, sistem mesajını chat'e ekle
      addMessage(
        "Belge sıfırlandı, artık varsayılan futbol dokümanıyla devam ediliyor.",
        "system-message"
      );
    } else {
      showErrorModal("Reset işlemi başarısız oldu.");
    }
  } catch (error) {
    console.error("Reset işlemi hatası:", error);
    showErrorModal("Reset işlemi sırasında bir hata oluştu.");
  }
}

// Hata modalı gösterme fonksiyonu (Modern hata bildirimi)
function showErrorModal(errorMessage) {
  // Var olan hata modalı varsa kaldır
  let existingModal = document.getElementById("error-modal");
  if (existingModal) {
    existingModal.remove();
  }
  // Modal konteynerini oluştur
  let modal = document.createElement("div");
  modal.id = "error-modal";
  modal.className = "modal";

  // Modal içerik kutusunu oluştur
  let modalContent = document.createElement("div");
  modalContent.className = "modal-content";

  // Hata mesajı paragrafı
  let p = document.createElement("p");
  p.innerText = errorMessage;

  // Modal buton kapsayıcısı oluştur
  let btnContainer = document.createElement("div");
  btnContainer.className = "modal-buttons";

  // "Tamam" butonunu oluştur
  let okButton = document.createElement("button");
  okButton.innerText = "Tamam";
  okButton.onclick = function () {
    modal.style.display = "none";
    modal.remove();
  };

  btnContainer.appendChild(okButton);
  modalContent.appendChild(p);
  modalContent.appendChild(btnContainer);
  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  modal.style.display = "block";
}

// 🚀 Enter tuşu ile mesaj gönderme
function handleKeyPress(event) {
  if (event.key === "Enter") sendMessage();
}

// Mesaj gönderme fonksiyonu (SESSION entegrasyonlu)
async function sendMessage(userInput = null) {
  let inputField = document.getElementById("user-input");
  let userMessage = userInput || inputField.value;

  if (!userMessage.trim()) return;

  addMessage(userMessage, "user-message");

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
    if (!currentSessionId && data.id) {
      currentSessionId = data.id;
    }
    fetchSessions();
    if (currentSessionId) {
      loadSession(currentSessionId);
    }
  } catch (error) {
    console.error("Error sending message:", error);
  }

  inputField.value = "";
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

// Bot mesajını seslendirme butonu ekleme
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

  let isSpeaking = false;
  let isPaused = false;

  speakBtn.onclick = () => {
    if (!isSpeaking) {
      speechSynthesis.cancel();
      speechSynthesis.speak(utterance);
      isSpeaking = true;
      isPaused = false;
    } else if (!isPaused) {
      speechSynthesis.cancel();
      isPaused = true;
    } else {
      speechSynthesis.cancel();
      speechSynthesis.speak(utterance);
      isPaused = false;
    }
  };

  messageDiv.appendChild(speakBtn);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// --- OTURUM YÖNETİMİ KISMI ---

function fetchSessions() {
  fetch("/sessions")
    .then((response) => response.json())
    .then((data) => {
      renderSessionList(data);
    })
    .catch((error) => console.error("Error fetching sessions:", error));
}

function renderSessionList(sessions) {
  let container = document.getElementById("chat-history");
  container.innerHTML = "";
  sessions.forEach((session) => {
    let sessionDiv = document.createElement("div");
    sessionDiv.className = "session-item";

    let titleSpan = document.createElement("span");
    titleSpan.textContent = session.title;

    let deleteBtn = document.createElement("button");
    deleteBtn.innerHTML = '<span style="color:red;">🗑️</span>';
    deleteBtn.className = "delete-btn";
    deleteBtn.onclick = (e) => {
      e.stopPropagation();
      deleteSession(session.id);
    };

    let renameBtn = document.createElement("button");
    renameBtn.innerHTML = '<span style="color:yellow;">✏️</span>';
    renameBtn.className = "rename-btn";
    renameBtn.onclick = (e) => {
      e.stopPropagation();
      showRenameModal(session.id, session.title);
    };

    sessionDiv.onclick = () => {
      loadSession(session.id);
    };

    sessionDiv.appendChild(titleSpan);
    sessionDiv.appendChild(renameBtn);
    sessionDiv.appendChild(deleteBtn);
    container.appendChild(sessionDiv);
  });
}

function loadSession(sessionId) {
  fetch(`/sessions/${sessionId}`)
    .then((response) => response.json())
    .then((data) => {
      currentSessionId = data.id;
      renderSessionMessages(data.messages);
    })
    .catch((error) => console.error("Error loading session:", error));
}

function renderSessionMessages(messages) {
  let chatBox = document.getElementById("chat-box");
  chatBox.innerHTML = "";
  messages.forEach((msg) => {
    if (msg.role === "assistant_image") {
      addImageToChat(msg.content);
    } else if (msg.role === "assistant_audio") {
      addAudioToChat(msg.content);
    } else {
      let className = msg.role === "user" ? "user-message" : "bot-message";
      addMessage(msg.content, className);
    }
  });
}

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
      setTimeout(listenForQuery, 500);
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
      setTimeout(() => recognition.start(), 1000);
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

function deleteSession(sessionId) {
  showDeleteConfirmation(sessionId);
}

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

function addImageToChat(base64Data) {
  let chatBox = document.getElementById("chat-box");
  let messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";

  let img = document.createElement("img");
  img.src = "data:image/png;base64," + base64Data;
  img.alt = "AI tarafından oluşturulmuş görsel";
  messageDiv.appendChild(img);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function addAudioToChat(base64Data) {
  let chatBox = document.getElementById("chat-box");
  let messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";

  let audio = document.createElement("audio");
  audio.controls = true;
  audio.src = "data:audio/wav;base64," + base64Data;
  messageDiv.appendChild(audio);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}
