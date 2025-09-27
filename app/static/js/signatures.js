document.addEventListener("DOMContentLoaded", function() {
    const loader = document.getElementById('pdf-loader');
    const pdfContainer = document.getElementById('pdf-container');
    loader.style.display = "flex";
    pdfContainer.style.display = "none";

    // construction de l'URL du PDF à partir du nom de fichier
    const filename = pdfContainer.getAttribute('data-filename');
    const url = `/signature/download/${filename}`;

    // Handler for rendering a page
    function handlePageRender(pageNum, numPages, loader, pdfContainer, page, scale) {
        const viewport = page.getViewport({ scale: scale });

        // Créer un conteneur pour cette page
        const pageDiv = document.createElement('div');
        pageDiv.className = 'pdf-page';
        pageDiv.style.marginBottom = '10px';
        
        // Préparation du canvas
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        pageDiv.appendChild(canvas);
        pdfContainer.appendChild(pageDiv);

        // Rendu de la page
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        page.render(renderContext).promise.then(function() {
            // Si c'est la dernière page, masquer le loader
            if (pageNum === numPages) {
                loader.style.display = "none";
                pdfContainer.style.display = "block";
            }
        });
    }

    // Fonction pour rendre une page
    function renderPage(pdf, pageNum, numPages, loader, pdfContainer, scale) {
        pdf.getPage(pageNum).then(function(page) {
            handlePageRender(pageNum, numPages, loader, pdfContainer, page, scale);
        });
    }

    // Chargement du PDF avec PDF.js
    const loadingTask = pdfjsLib.getDocument(url);
    loadingTask.promise.then(function(pdf) {
        const scale = 1.5;
        const numPages = pdf.numPages;
        
        // Vider le conteneur
        pdfContainer.innerHTML = '';
        
        // Rendre toutes les pages
        for (let pageNum = 1; pageNum <= numPages; pageNum++) {
            renderPage(pdf, pageNum, numPages, loader, pdfContainer, scale);
        }
        
    }, function(reason) {
        // Erreur lors du chargement du PDF
        console.error(reason);
    });
});