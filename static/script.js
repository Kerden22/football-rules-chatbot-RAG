// =====================================
// 1. Global State ve Sayfa Yükleme
// =====================================

// Aktif oturumun ID’si
let currentSessionId = null;

window.addEventListener("load", () => {
  fetchSessions(); // Mevcut oturumları getir
  document.getElementById("new-chat-btn").addEventListener("click", () => {
    currentSessionId = null;
    document.getElementById("chat-box").innerHTML = "";
    document.getElementById("user-input").value = "";
  });
});

// =====================================
// 2. Doküman Yükleme ve Sıfırlama
// =====================================

/**
 * Kullanıcının seçtiği dosyayı sunucuya yükler ve yeni oturum başlatır.
 */
async function uploadDocument() {
  const fileInput = document.getElementById("document-input");
  const spinner = document.getElementById("upload-spinner");

  if (!fileInput.files.length) {
    showErrorModal("Lütfen bir dosya seçin!");
    return;
  }

  const file = fileInput.files[0];
  const allowedTypes = [
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];
  if (!allowedTypes.includes(file.type)) {
    showErrorModal("Yalnızca PDF, TXT veya DOCX yükleyebilirsiniz.");
    return;
  }

  spinner.style.display = "block"; // Yükleme sırasında spinner göster

  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/upload-document", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (data.session_id) {
      currentSessionId = data.session_id;
      addMessage(
        "Belge başarıyla yüklendi ve işlendi. Artık soru sorabilirsiniz.",
        "system-message"
      );
      fetchSessions(); // Oturum listesini güncelle
    } else {
      showErrorModal("Belge işleme sırasında bir sorun oluştu.");
    }
  } catch (err) {
    console.error(err);
    showErrorModal("Dosya yüklenirken bir hata oluştu.");
  } finally {
    spinner.style.display = "none"; // Spinner’ı gizle
  }
}

/**
 * Seçili oturumdaki doküman verisini sıfırlar.
 */
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

// =====================================
// 3. Hata ve Bilgilendirme Modalları
// =====================================

/**
 * Ekrana hata mesajı içeren modal gösterir.
 * @param {string} errorMessage - Kullanıcıya gösterilecek hata metni
 */
function showErrorModal(errorMessage) {
  let existing = document.getElementById("error-modal");
  if (existing) existing.remove();

  let modal = document.createElement("div");
  modal.id = "error-modal";
  modal.className = "modal";

  let content = document.createElement("div");
  content.className = "modal-content";

  let p = document.createElement("p");
  p.innerText = errorMessage;

  let btnContainer = document.createElement("div");
  btnContainer.className = "modal-buttons";

  let okBtn = document.createElement("button");
  okBtn.innerText = "Tamam";
  okBtn.onclick = () => {
    modal.remove();
  };

  btnContainer.appendChild(okBtn);
  content.appendChild(p);
  content.appendChild(btnContainer);
  modal.appendChild(content);
  document.body.appendChild(modal);

  modal.style.display = "block"; // Modal’ı görünür yap
}

// =====================================
// 4. Mesaj Gönderme ve Klavye Kısayolu
// =====================================

/**
 * Enter tuşu ile mesaj gönderimini tetikler.
 */
function handleKeyPress(event) {
  if (event.key === "Enter") sendMessage();
}

/**
 * Kullanıcı mesajını sunucuya yollar ve oturumu günceller.
 * @param {string|null} userInput - Manuel geçirilen mesaj, yoksa input alanından alır
 */
async function sendMessage(userInput = null) {
  const inputField = document.getElementById("user-input");
  const userMessage = (userInput || inputField.value).trim();
  if (!userMessage) return;

  addMessage(userMessage, "user-message");

  const url = currentSessionId
    ? `/sessions/${currentSessionId}/messages`
    : "/sessions";

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userMessage }),
    });
    const data = await response.json();
    if (!currentSessionId && data.id) {
      currentSessionId = data.id; // Yeni oturum ID’si ata
    }
    fetchSessions();
    if (currentSessionId) loadSession(currentSessionId);
  } catch (err) {
    console.error("Error sending message:", err);
  }

  inputField.value = ""; // Gönderimden sonra alanı temizle
}

// =====================================
// 5. Mesaj Balonları Ekleme
// =====================================

/**
 * Kullanıcı veya sistem mesajını sohbet kutusuna ekler.
 */
function addMessage(text, className) {
  const chatBox = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = `message ${className}`;
  div.innerText = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight; // Kaydırmayı en alta getir
}

/**
 * Bot cevabını ve geri bildirim ikonlarını gösterir.
 * @param {string} answerText - Bot cevabı
 * @param {string} questionText - Kullanıcı sorusu (feedback için)
 */
function addBotMessage(answerText, questionText) {
  const chatBox = document.getElementById("chat-box");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";

  const p = document.createElement("p");
  p.innerText = answerText;
  messageDiv.appendChild(p);

  const iconsDiv = document.createElement("div");
  iconsDiv.className = "feedback-icons";
  iconsDiv.innerHTML = `
    <button class="like-btn">👍</button>
    <button class="dislike-btn">👎</button>
  `;
  messageDiv.appendChild(iconsDiv);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  const formDiv = document.createElement("div");
  formDiv.className = "feedback-form";
  formDiv.style.display = "none";
  formDiv.innerHTML = `
    <textarea placeholder="Neyi beğenmediniz?"></textarea>
    <button class="send-feedback-btn">Gönder</button>
  `;
  chatBox.appendChild(formDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  const likeBtn = iconsDiv.querySelector(".like-btn");
  const dislikeBtn = iconsDiv.querySelector(".dislike-btn");
  const sendBtn = formDiv.querySelector(".send-feedback-btn");

  likeBtn.addEventListener("click", () => {
    submitFeedback("like", questionText, answerText, null, formDiv, null);
  });
  dislikeBtn.addEventListener("click", () => {
    formDiv.style.display = "flex"; // Dislike tıklanınca textarea göster
  });
  sendBtn.addEventListener("click", () => {
    const ta = formDiv.querySelector("textarea");
    submitFeedback(
      "dislike",
      questionText,
      answerText,
      ta.value.trim(),
      formDiv,
      ta
    );
  });
}

// =====================================
// 6. Geri Bildirim Gönderme
// =====================================

/**
 * Kullanıcı geri bildirimini API’ye POST eder.
 * @param {string} type - "like" veya "dislike"
 * @param {string} question - Kullanıcı sorusu
 * @param {string} answer - Bot cevabı
 * @param {string|null} feedbackText - Opsiyonel detaylı yorum
 * @param {HTMLElement} formDiv - Geri bildirim formu container
 * @param {HTMLTextAreaElement|null} textareaElem - Geri bildirim textarea’sı
 */
function submitFeedback(
  type,
  question,
  answer,
  feedbackText,
  formDiv,
  textareaElem
) {
  if (type === "dislike" && !feedbackText) {
    showToast("Lütfen geri bildiriminizi yazın.", "error");
    return;
  }

  const payload = {
    session_id: currentSessionId,
    question,
    answer,
    feedback_text: feedbackText,
  };

  fetch("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then((res) => {
      if (!res.ok) throw new Error("Gönderim hatası");
      showToast("Geri bildiriminiz için teşekkür ederiz!", "success");
      if (formDiv && textareaElem) {
        formDiv.style.display = "none";
        textareaElem.value = "";
      }
    })
    .catch((err) => {
      console.error(err);
      showToast("Geri bildirim gönderilirken hata oluştu.", "error");
    });
}

// =====================================
// 7. Oturum Yönetimi ve Listeleme
// =====================================

/**
 * Oturum listesini API’den alır.
 */
function fetchSessions() {
  fetch("/sessions")
    .then((res) => res.json())
    .then((data) => renderSessionList(data))
    .catch((err) => console.error("Error fetching sessions:", err));
}

/**
 * Oturumları soldaki listede render eder.
 */
function renderSessionList(sessions) {
  const container = document.getElementById("chat-history");
  container.innerHTML = "";
  sessions.forEach((s) => {
    const div = document.createElement("div");
    div.className = "session-item";
    div.innerHTML = `
      <span>${s.title}</span>
      <button class="rename-btn">✏️</button>
      <button class="delete-btn">🗑️</button>
    `;
    div.addEventListener("click", () => loadSession(s.id));
    div.querySelector(".delete-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      deleteSession(s.id);
    });
    div.querySelector(".rename-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      showRenameModal(s.id, s.title);
    });
    container.appendChild(div);
  });
}

/**
 * Seçili oturumu yükleyip mesajlarını gösterir.
 */
function loadSession(sessionId) {
  fetch(`/sessions/${sessionId}`)
    .then((res) => res.json())
    .then((data) => {
      currentSessionId = data.id;
      renderSessionMessages(data.messages);
    })
    .catch((err) => console.error("Error loading session:", err));
}

/**
 * Bir oturumdaki tüm mesajları chat kutusuna render eder.
 */
function renderSessionMessages(messages) {
  const chatBox = document.getElementById("chat-box");
  chatBox.innerHTML = "";

  let lastUserText = "";
  messages.forEach((msg) => {
    if (msg.role === "user") {
      addMessage(msg.content, "user-message");
      lastUserText = msg.content;
    } else if (msg.role === "assistant") {
      addBotMessage(msg.content, lastUserText);
    } else if (msg.role === "assistant_image") {
      addImageToChat(msg.content);
    } else if (msg.role === "assistant_audio") {
      addAudioToChat(msg.content);
    } else {
      addMessage(msg.content, "system-message");
    }
  });
}

// =====================================
// 8. Görsel ve Ses Öğeleri
// =====================================

/**
 * Base64 görseli chat’e <img> olarak ekler.
 */
function addImageToChat(base64Data) {
  const chatBox = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = "message bot-message";
  const img = document.createElement("img");
  img.src = "data:image/png;base64," + base64Data; // Inline base64
  img.alt = "AI tarafından oluşturulmuş görsel";
  div.appendChild(img);
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Base64 ses dosyasını chat’e <audio> olarak ekler.
 */
function addAudioToChat(base64Data) {
  const chatBox = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = "message bot-message";
  const audio = document.createElement("audio");
  audio.controls = true;
  audio.src = "data:audio/wav;base64," + base64Data; // Inline base64
  div.appendChild(audio);
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// =====================================
// 9. Oturum Silme ve Yenileme Modalları
// =====================================

function deleteSession(sessionId) {
  showDeleteConfirmation(sessionId);
}

function showDeleteConfirmation(sessionId) {
  const modal = document.getElementById("confirm-modal");
  modal.style.display = "block";

  const yesOld = document.getElementById("confirm-yes");
  const noOld = document.getElementById("confirm-no");

  const yesBtn = yesOld.cloneNode(true);
  yesOld.parentNode.replaceChild(yesBtn, yesOld);
  const noBtn = noOld.cloneNode(true);
  noOld.parentNode.replaceChild(noBtn, noOld);

  yesBtn.onclick = () => {
    fetch(`/sessions/${sessionId}`, { method: "DELETE" })
      .then((res) => {
        if (res.ok) {
          fetchSessions();
          document.getElementById("chat-box").innerHTML = "";
          currentSessionId = null;
        } else {
          alert("Silme işlemi başarısız oldu.");
        }
      })
      .catch((err) => console.error("Error deleting session:", err));
    modal.style.display = "none";
  };

  noBtn.onclick = () => {
    modal.style.display = "none";
  };
}

function showRenameModal(sessionId, currentTitle) {
  const modal = document.getElementById("rename-modal");
  modal.style.display = "block";

  const input = document.getElementById("rename-input");
  input.value = currentTitle;

  const yesOld = document.getElementById("rename-yes");
  const noOld = document.getElementById("rename-no");

  const yesBtn = yesOld.cloneNode(true);
  yesOld.parentNode.replaceChild(yesBtn, yesOld);
  const noBtn = noOld.cloneNode(true);
  noOld.parentNode.replaceChild(noBtn, noOld);

  yesBtn.onclick = () => {
    const newTitle = input.value.trim();
    if (!newTitle) {
      modal.style.display = "none";
      return;
    }
    fetch(`/sessions/${sessionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.newTitle) fetchSessions();
      })
      .catch((err) => console.error("Error renaming:", err));
    modal.style.display = "none";
  };

  noBtn.onclick = () => {
    modal.style.display = "none";
  };
}

// =====================================
// 10. Sesli Asistan Özelliği
// =====================================

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
    if (transcript.includes("asistan") && !isListeningForQuery) {
      isListeningForQuery = true;
      recognition.stop();
      setTimeout(listenForQuery, 500);
    }
  };
  recognition.onerror = (err) => console.error("Ses Tanıma Hatası:", err);
  recognition.start();

  function listenForQuery() {
    const qr = new SpeechRecognition();
    qr.lang = "tr-TR";
    qr.continuous = false;
    qr.interimResults = false;
    qr.start();

    qr.onresult = (event) => {
      const userQuery = event.results[0][0].transcript;
      sendMessage(userQuery);
      isListeningForQuery = false;
      setTimeout(() => recognition.start(), 1000);
    };
    qr.onerror = (err) => {
      console.error("Soru Tanıma Hatası:", err);
      isListeningForQuery = false;
      setTimeout(() => recognition.start(), 1000);
    };
  }

  voiceBtn.onclick = () => listenForQuery();
});

// =====================================
// 11. Toast Bildirimleri
// =====================================

/**
 * Ekranın köşesinde kısa süreli bildirim gösterir.
 * @param {string} message - Gösterilecek metin
 * @param {"success"|"error"} type - Bildirim türü
 */
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => {
    container.removeChild(toast);
  }, 3000); // 3 saniye sonra temizle
}
