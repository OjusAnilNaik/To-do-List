const addBtn = document.getElementById("addBtn");
const input = document.getElementById("taskInput");
const list = document.getElementById("taskList");
const clearAllBtn = document.getElementById("clearAll");
const colorPicker = document.getElementById("colorPicker");
const themeToggle = document.getElementById("themeToggle");
const emojiBtn = document.getElementById("emojiBtn");
const emojiPanel = document.getElementById("emojiPanel");

const filterBtns = document.querySelectorAll(".filter-btn");
let currentFilter = "all";

let notes = JSON.parse(localStorage.getItem("notes")) || [];

// Emoji picker setup
const emojis = ["😀","😁","😂","🤣","😊","😍","😎","🤔","😢","😭","😡","👍","👏","🙏","🔥","⭐","💡","✅","❤️","🌸","☀️","🌙","⚡","💬"];

function showEmojiPanel() {
  emojiPanel.innerHTML = "";
  emojis.forEach(e => {
    const span = document.createElement("span");
    span.textContent = e;
    span.style.cursor = "pointer";
    span.onclick = () => {
      input.value += e;
      emojiPanel.classList.add("hidden");
    };
    emojiPanel.appendChild(span);
  });
  emojiPanel.classList.toggle("hidden");
}
emojiBtn.onclick = showEmojiPanel;

document.addEventListener("click", e => {
  if (!emojiPanel.contains(e.target) && e.target !== emojiBtn)
    emojiPanel.classList.add("hidden");
});

function renderNotes() {
  list.innerHTML = "";

  let filteredNotes = notes;
  if (currentFilter === "pinned") filteredNotes = notes.filter(n => n.pinned);
  else if (currentFilter === "done") filteredNotes = notes.filter(n => n.done);
  else if (currentFilter === "notdone") filteredNotes = notes.filter(n => !n.done);

  filteredNotes.sort((a, b) => b.pinned - a.pinned);

  filteredNotes.forEach((note, index) => {
    const li = document.createElement("li");
    li.style.borderLeftColor = note.color;
    if (note.pinned) li.classList.add("pinned");

    const textDiv = document.createElement("div");
    textDiv.classList.add("note-text");
    textDiv.innerHTML = note.text;
    textDiv.onclick = () => toggleDone(index);
    textDiv.contentEditable = false;

    const timeDiv = document.createElement("small");
    timeDiv.innerHTML = `
      Created: ${new Date(note.createdAt).toLocaleString()}<br>
      Last Edited: ${new Date(note.updatedAt).toLocaleString()}
    `;

    const actions = document.createElement("div");
    actions.classList.add("actions");

    const pinBtn = document.createElement("button");
    pinBtn.textContent = note.pinned ? "📌 Unpin" : "📍 Pin";
    pinBtn.classList.add("pin");
    pinBtn.onclick = () => togglePin(index);

    const editBtn = document.createElement("button");
    editBtn.textContent = "✏️ Edit";
    editBtn.classList.add("edit");
    editBtn.onclick = () => editNote(index, textDiv, editBtn);

    const speakBtn = document.createElement("button");
    speakBtn.textContent = "🔊 Read";
    speakBtn.classList.add("speak");
    speakBtn.onclick = () => speak(note.text);

    const delBtn = document.createElement("button");
    delBtn.textContent = "🗑️";
    delBtn.classList.add("delete");
    delBtn.onclick = () => deleteNote(index);

    if (note.done) {
      const doneEmoji = document.createElement("span");
      doneEmoji.textContent = "✅";
      doneEmoji.classList.add("done-mark");
      li.appendChild(doneEmoji);
    }

    actions.append(pinBtn, editBtn, speakBtn, delBtn);
    li.append(textDiv, timeDiv, actions);
    list.appendChild(li);
  });
}

function addNote() {
  const val = input.value.trim();
  if (!val) return alert("Write something!");
  const timestamp = new Date().toISOString();
  const newNote = {
    text: val,
    color: colorPicker.value,
    pinned: false,
    done: false,
    createdAt: timestamp,
    updatedAt: timestamp
  };
  notes.push(newNote);
  input.value = "";
  saveNotes();
}

function toggleDone(index) {
  notes[index].done = !notes[index].done;
  saveNotes();
}

function deleteNote(index) {
  notes.splice(index, 1);
  saveNotes();
}

function togglePin(index) {
  notes[index].pinned = !notes[index].pinned;
  notes[index].updatedAt = new Date().toISOString();
  saveNotes();
}

function editNote(index, textDiv, button) {
  const note = notes[index];
  if (textDiv.contentEditable === "true") {
    note.text = textDiv.innerText.trim();
    note.updatedAt = new Date().toISOString();
    button.textContent = "✏️ Edit";
    textDiv.contentEditable = false;
    saveNotes();
  } else {
    textDiv.contentEditable = true;
    textDiv.focus();
    button.textContent = "💾 Save";
  }
}

function speak(text) {
  const speech = new SpeechSynthesisUtterance(text);
  speech.lang = "en-US";
  speech.rate = 1;
  window.speechSynthesis.speak(speech);
}

function saveNotes() {
  localStorage.setItem("notes", JSON.stringify(notes));
  renderNotes();
}

clearAllBtn.onclick = () => {
  if (confirm("Clear all notes?")) {
    notes = [];
    saveNotes();
  }
};

themeToggle.onclick = () => {
  document.body.classList.toggle("dark");
  themeToggle.textContent = document.body.classList.contains("dark") ? "☀️" : "🌙";
  localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
};

if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
  themeToggle.textContent = "☀️";
}

filterBtns.forEach(btn => {
  btn.onclick = () => {
    filterBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.id.replace("filter", "").toLowerCase();
    renderNotes();
  };
});

addBtn.onclick = addNote;
input.addEventListener("keypress", e => e.key === "Enter" && addNote());

renderNotes();