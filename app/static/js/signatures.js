const signaturePoints = [];
const container = document.getElementById('pdf-container');
const formContainer = document.getElementById('signer-form');

pdfjsLib.getDocument(PDF_URL).promise.then(pdf => {
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        pdf.getPage(pageNum).then(page => {
        const viewport = page.getViewport({ scale: 1.5 });
        const canvas = document.createElement('canvas');
        canvas.classList.add('pdf-page');
        canvas.dataset.pageNumber = pageNum;
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        const context = canvas.getContext('2d');
        page.render({ canvasContext: context, viewport: viewport });

        canvas.addEventListener('click', function(e) {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const page = parseInt(canvas.dataset.pageNumber);

            const index = signaturePoints.length;
            signaturePoints.push({ x, y, page });

            // Créer le menu déroulant
            const div = document.createElement('div');
            div.innerHTML = `
            <label>Signataire pour point ${index + 1} (Page ${page})</label>
            <select name="signer_${index}" required>
                ${users.map(u => `<option value="${u.id}">${u.name}</option>`).join('')}
            </select>
            <input type="hidden" name="x_${index}" value="${x}">
            <input type="hidden" name="y_${index}" value="${y}">
            <input type="hidden" name="page_${index}" value="${page}">
            `;
            formContainer.appendChild(div);

            // Marqueur visuel
            const marker = document.createElement('div');
            marker.style.position = 'absolute';
            marker.style.left = `${canvas.offsetLeft + x}px`;
            marker.style.top = `${canvas.offsetTop + y}px`;
            marker.style.width = '10px';
            marker.style.height = '10px';
            marker.style.background = 'red';
            marker.style.borderRadius = '50%';
            marker.style.zIndex = '10';
            marker.style.pointerEvents = 'none';
            document.body.appendChild(marker);
        });

        container.appendChild(canvas);
        });
    }
});
