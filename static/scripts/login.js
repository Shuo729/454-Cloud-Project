function navigate(event) {
  event.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!username || !password) {
    alert("Please enter both username and password.");
    return;
  }

  fetch('/login-form', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      window.location.href = data.redirect;
    } 
    else {
      alert(data.error || "Invalid credentials.");
    }
  })
  .catch(error => {
    console.error(error);
    alert("Login failed. Please try again.");
  });
}

document.getElementById('login-form').addEventListener('submit', navigate);
