function previewImage(event) {
    const input = event.target;
    const preview = document.getElementById('preview');
    const button = document.getElementById('upload-button');
    const label = document.getElementById('photo-label');

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };

        button.style.display = 'block'
        label.style.display = 'none'

        reader.readAsDataURL(input.files[0]);
    } else {
        preview.src = '#';
        preview.style.display = 'none';
    }
}