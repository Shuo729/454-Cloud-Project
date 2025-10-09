function navigate(event) {
  event.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!username || !password) {
    alert("Please enter both username and password.");
    return;
  }

  fetch('/signup-form', {
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
      alert(data.error || "Signup failed. Please try again.");
    }
  })
  .catch(error => {
    console.error(error);
    alert("Signup failed. Please try again.");
  });
}

document.getElementById('signup-form').addEventListener('submit', navigate);
