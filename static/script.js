document.getElementById('qr-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const url = document.getElementById('url').value;
    const expires = document.getElementById('expires').value;

    fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url, expires: expires })
    })
    .then(response => response.json())
    .then(data => {
        if (data.qr_code_url) {
            document.getElementById('qr-code').src = data.qr_code_url;
        } else {
            alert('Error generating QR code: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
