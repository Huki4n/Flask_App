
// Функция добавления названия файла в инпут
function displayFileName(id_input, id_file_name, id_delete_icon) {
    const fileInput = document.getElementById(id_input);
    const fileNameDisplay = document.getElementById(id_file_name);
    const deleteFileIcon = document.getElementById(id_delete_icon);

    if (fileInput.files.length > 0) {
      const fileName = fileInput.files[0].name;
      fileNameDisplay.textContent = `${fileName}`;
      deleteFileIcon.style.display = 'inline'
    } else {
      fileNameDisplay.textContent = 'Upload post image';
      deleteFileIcon.style.display = 'none'
    }
}

// Функция удаления названия файла из инпута
function deleteFile(event, id_input, id_file_name, id_delete_icon){
    event.stopPropagation()
    event.preventDefault()

    const fileInput = document.getElementById('file');
    fileInput.value = ''

    displayFileName(id_input, id_file_name, id_delete_icon)
}

// Функция для добавления предварительного просмотра изображения
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

function openModal(id, element) {
    document.getElementById(id).style.display = "flex";

    // Загрузка данных в форму при открытии модалки редактирования
    // сделал так, потому что не получалось пробросить post в edit_modal
    if(id === 'editPostModal') {
        const post = JSON.parse(atob(element.getAttribute('data-post')));

        const titleInput = document.getElementById('edit-title');
        const contentInput = document.getElementById('edit-content');
        const postIdInput = document.getElementById('hidden-input-post-id');
        const fileNameDisplay = document.getElementById('edit-file-name');
        const fileEditInput = document.getElementById('file-edit');
        const fileName = document.getElementById('hidden-input-image-url');

        postIdInput.value = post.id
        titleInput.value = post.title
        contentInput.value = post.content

        if(post.image_url) {
            fileEditInput.files[0] = post.image_url
            fileName.value = post.image_url
            fileNameDisplay.textContent = post.image_url.replace("uploads/", "")
        }

        const editTagsList = document.getElementById('edit-tags-list');
        const editHiddenTags = document.getElementById('edit-hidden-tags');

        let postTags = post.tags

        // Добавляем теги в список
        postTags.forEach(tag => {
            if (tag) {
                const li = document.createElement('li');
                li.classList.add('tag');
                li.innerHTML = `
                    <div>${tag}</div> 
                    <span onclick="deleteTag(this, 'edit-')" class="delete-tag">&times;</span>
                `;
                editTagsList.appendChild(li);
            }
        });

        // Получаем массив названий тегов
        const existingTags = Array.from(editTagsList.getElementsByClassName('tag'))
            .map(tag => tag.querySelector('div:first-child').textContent.trim());

        // Заполняем скрытое поле тегов
        editHiddenTags.value = JSON.stringify(existingTags);
    }
}

// Функция закрытия модалки
function closeModal(id) {
    document.getElementById(id).style.display = "none";

    const existingTags = Array.from(document.getElementsByClassName('tag'));
    existingTags.forEach(tag => tag.remove());
    document.getElementById('tag-input').value = '';
    document.getElementById('edit-tag-input').value = '';
}

// Функция отправки формы для редактирования поста
function handleSubmitEditPostForm(event){
    event.preventDefault();

    const postId = document.getElementById('hidden-input-post-id').value;
    const url = `/edit_post/${postId}`

    const form = document.getElementById('editPostForm');
    form.action = url;

    form.submit();
}

// Функция отправки формы для удаления поста
function handleSubmitDeletePostForm(event){
    event.preventDefault();

    const postId = document.getElementById('hidden-input-post-id').value;
    const url = `/delete_post/${postId}`

    const form = document.getElementById('deletePostForm');
    form.action = url;

    form.submit();
}

// Функция для удаления тега
function deleteTag(element, type='') {
    const tagElement = element.closest('.tag');
    console.log(tagElement)
    const tagValue = tagElement.querySelector('div').textContent.trim();

    const hiddenInput = document.getElementById(`${type}hidden-tags`);

    let tagsArray= JSON.parse(hiddenInput.value);
    if (!Array.isArray(tagsArray)) throw new Error("Not an array");

    tagsArray = tagsArray.filter(tag => String(tag) !== String(tagValue));

    hiddenInput.value = JSON.stringify(tagsArray);

    tagElement.remove();
}

// Функция для очисти ввода тега
function clearInput(){
    const tagInput = document.getElementById('tag-input')
    tagInput.value = ''
}

// Функция для добавления тега
function addTag(type= '') {
    const tagInput = document.getElementById(`${type}tag-input`);
    const error = document.getElementById(`${type}tags-error`);

    const tagName = tagInput.value.trim();
    if (!tagName) return;

    const tagsList = document.getElementById(`${type}tags-list`);

    // Получаем массив названий тегов
    const existingTags = Array.from(tagsList.getElementsByClassName('tag'))
        .map(tag => tag.querySelector('div:first-child').textContent.trim());

    // Проверка на количество тегов, максимум 4
    if(existingTags.length === 4) {
        error.style.display = 'flex'
        error.innerText = 'The maximum number of tags is 4'
        tagInput.value = '';
        return;
    }

    // Проверка на то, что тег уже существует
    if (existingTags.includes(tagName)) {
        tagInput.value = '';
        error.style.display = 'flex'
        error.innerText = 'Tag with this name already exist'
        return;
    }

    const tagElement = document.createElement('div');
    tagElement.classList.add('tag');
    tagElement.innerHTML = `
        <div>${tagName}</div>
        <span onclick="deleteTag(this, '${type}')" class="delete-tag">&times;</span>
    `;

    // Очищаем поле ошибки при успешном добавлении
    error.style.display = 'none'
    error.innerText = ''

    tagsList.appendChild(tagElement);
    // Добавляем значения в скрытый input
    existingTags.push(tagName)
    document.getElementById(`${type}hidden-tags`).value = JSON.stringify(existingTags);

    tagInput.value = '';
}
