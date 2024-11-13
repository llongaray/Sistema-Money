// Funções de Gerenciamento de Campanhas
function toggleCampanhaAction() {
    const acaoCampanha = document.getElementById('acaoCampanha').value;
    document.getElementById('editCampanhaSection').style.display = acaoCampanha === 'edit' ? 'block' : 'none';
    document.getElementById('importCampanhaSection').style.display = acaoCampanha === 'import' ? 'block' : 'none';
}

function autocompleteCampanha(value) {
    const campanhas = Object.keys(debitosPorCampanha).map(id => ({
        id: id,
        nome: document.querySelector(`option[value="${id}"]`).text,
        debitos: debitosPorCampanha[id]
    }));

    const campanha = campanhas.find(c => c.nome.toLowerCase().includes(value.toLowerCase()));
    const infoDiv = document.getElementById('campanhaInfo');

    if (campanha) {
        infoDiv.innerHTML = `
            <p>Status: ${campanha.status ? 'Ativo' : 'Inativo'}</p>
            <p>Débitos associados: ${campanha.debitos}</p>
            <label for="statusCampanha">Alterar Status:</label>
            <select id="statusCampanha">
                <option value="true" ${campanha.status ? 'selected' : ''}>Ativo</option>
                <option value="false" ${!campanha.status ? 'selected' : ''}>Inativo</option>
            </select>
        `;
    } else {
        infoDiv.innerHTML = '';
    }
}

function updateCampanha() {
    const statusCampanha = document.getElementById('statusCampanha').value;
    console.log(`Atualizando campanha para status: ${statusCampanha}`);
}

// Funções de Gerenciamento de Campos e Visibilidade
function toggleSetorField() {
    const tipoMeta = document.getElementById('tipo').value;
    const setorContainer = document.getElementById('setorContainer');
    const setorSelect = document.getElementById('setor');
    const lojaContainer = document.getElementById('lojaContainer');
    const lojaSelect = document.getElementById('loja');
    
    if (tipoMeta === 'EQUIPE') {
        setorContainer.style.display = 'block';
        setorSelect.required = true;
        
        if (setorSelect.value === 'INSS') {
            lojaContainer.style.display = 'block';
            lojaSelect.required = true;
        } else {
            lojaContainer.style.display = 'none';
            lojaSelect.required = false;
            lojaSelect.value = '';
        }
    } else {
        setorContainer.style.display = 'none';
        lojaContainer.style.display = 'none';
        setorSelect.required = false;
        lojaSelect.required = false;
        setorSelect.value = '';
        lojaSelect.value = '';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    const setorSelect = document.getElementById('setor');
    if (setorSelect) {
        setorSelect.addEventListener('change', function() {
            if (this.value === 'INSS') {
                document.getElementById('lojaContainer').style.display = 'block';
                document.getElementById('loja').required = true;
            } else {
                document.getElementById('lojaContainer').style.display = 'none';
                document.getElementById('loja').required = false;
                document.getElementById('loja').value = '';
            }
        });
    }

    // Inicialização
    toggleSetorField();
});
