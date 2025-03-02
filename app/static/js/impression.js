const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");

dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragover");

    const files = event.dataTransfer.files;
    handleFiles(files);
});

fileInput.addEventListener("change", (event) => {
    const files = event.target.files;
    handleFiles(files);
});

function handleFiles(files) {
    for (const file of files) {
        if (file.type === "application/pdf") {
            console.log("Fichier PDF téléchargé : ", file.name);
            uploadFile(file);
        } else {
            alert("Veuillez déposer ou sélectionner uniquement des fichiers PDF.");
        }
    }
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {  // Remplace '/upload' par l'URL de ton service d'impression
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        console.log("Fichier envoyé avec succès : ", data);
        alert("Fichier envoyé avec succès pour impression !");
    })
    .catch(error => {
        console.error("Erreur lors de l'envoi du fichier : ", error);
        alert("Erreur lors de l'envoi du fichier.");
    });
}
