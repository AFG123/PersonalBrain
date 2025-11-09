const form = document.getElementById('chat-form');
const input = document.getElementById('question');
const messages = document.getElementById('messages');

function addMessage(text, cls='bot'){
  const div = document.createElement('div');
  div.className = `message ${cls}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener('submit', async (e) => {
  const q = input.value.trim();
  if(!q) return;
  addMessage(q, 'user');
  input.value = '';

  addMessage('Thinking...', 'loading');

  try{
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });

    const data = await res.json();
    // remove the 'Thinking...' loading message
    const loading = document.querySelector('.message.loading');
    if(loading) loading.remove();

    if(data.error){
      addMessage('Error: ' + data.error, 'bot');
    } else {
      addMessage(data.answer, 'bot');
    }
  } catch(err){
    const loading = document.querySelector('.message.loading');
    if(loading) loading.remove();
    addMessage('Network error. See console for details.', 'bot');
    console.error(err);
  }
});

// Allow Enter to send
input.addEventListener('keydown', (e)=>{
  if(e.key === 'Enter'){
    form.dispatchEvent(new Event('submit'));
  }
});
