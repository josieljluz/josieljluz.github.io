// Configurações
const config = {
  metadataFile: 'files_metadata.json', // Arquivo gerado pelo workflow
  excludedFiles: ["index.html", ".gitignore", "README.md", "style.css", "script.js", "files_metadata.json"],
  itemsPerPage: 10,
  enablePagination: true
};

// Cache de arquivos
let filesCache = [];
let currentSort = 'name';
let currentPage = 1;

// Elementos DOM
const fileList = document.getElementById('file-list');
const searchInput = document.getElementById('search');
const sortSelect = document.getElementById('sort');

// Funções de formatação
const formatBytes = (bytes) => {
  if (typeof bytes !== 'number' || isNaN(bytes)) return 'Tamanho desconhecido';
  
  const sizes = ["B", "KB", "MB", "GB"];
  if (bytes === 0) return "0 B";
  const i = Math.min(parseInt(Math.floor(Math.log(bytes) / Math.log(1024)), 10), sizes.length - 1);
  return (bytes / Math.pow(1024, i)).toFixed(2) + " " + sizes[i];
};

const formatDate = (isoString) => {
  if (!isoString) return 'Data desconhecida';
  
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString("pt-BR") + " " + date.toLocaleTimeString("pt-BR");
  } catch (e) {
    console.error('Erro ao formatar data:', e);
    return 'Data inválida';
  }
};

const getFileIcon = (filename) => {
  const extension = filename.split('.').pop().toLowerCase();
  const icons = {
    pdf: '📄',
    doc: '📝', docx: '📝',
    xls: '📊', xlsx: '📊',
    ppt: '📊', pptx: '📊',
    txt: '📑',
    zip: '🗜️', rar: '🗜️', '7z': '🗜️',
    exe: '⚙️', msi: '⚙️',
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', svg: '🖼️',
    mp3: '🎵', wav: '🎵',
    mp4: '🎬', avi: '🎬', mkv: '🎬',
    default: '📁'
  };
  
  return icons[extension] || icons.default;
};

// Funções de ordenação e paginação (mantidas iguais)
// ... (manter as mesmas funções sortFiles, paginateFiles, renderPagination)

// Renderização (modificada para usar dados locais)
const renderFiles = (files) => {
  if (!files || files.length === 0) {
    fileList.innerHTML = '<li class="error-message">Nenhum arquivo encontrado.</li>';
    document.getElementById('pagination-controls').innerHTML = '';
    return;
  }
  
  const sortedFiles = sortFiles(files, currentSort);
  const filesToRender = config.enablePagination 
    ? paginateFiles(sortedFiles, currentPage, config.itemsPerPage)
    : sortedFiles;
  
  fileList.innerHTML = '';
  
  filesToRender.forEach(file => {
    const li = document.createElement('li');
    
    const link = document.createElement('a');
    link.href = file.path; // Usar path relativo
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.innerHTML = `<span class="file-icon">${file.icon}</span> ${file.name}`;
    
    const details = document.createElement('div');
    details.className = 'file-details';
    details.innerHTML = `
      <span>📏 ${file.size}</span>
      <span>🕒 ${file.lastModified}</span>
    `;
    
    li.appendChild(link);
    li.appendChild(details);
    fileList.appendChild(li);
  });
  
  if (config.enablePagination) {
    renderPagination(files.length, currentPage, config.itemsPerPage);
  }
};

// Filtragem (mantida igual)
const filterFiles = (searchTerm) => {
  currentPage = 1;
  
  if (!searchTerm) {
    renderFiles(filesCache);
    return;
  }
  
  const term = searchTerm.toLowerCase();
  const filtered = filesCache.filter(file => 
    file.name.toLowerCase().includes(term)
  );
  
  renderFiles(filtered);
};

// Event listeners (mantidos iguais)
const setupEventListeners = () => {
  searchInput.addEventListener('input', (e) => {
    filterFiles(e.target.value);
  });
  
  sortSelect.addEventListener('change', (e) => {
    currentSort = e.target.value;
    renderFiles(filesCache);
  });
  
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('pagination-button')) {
      e.preventDefault();
      const page = parseInt(e.target.dataset.page);
      if (!isNaN(page) && page !== currentPage) {
        currentPage = page;
        renderFiles(filesCache);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  });
};

// Carregar metadados dos arquivos
const loadFilesMetadata = async () => {
  try {
    const response = await fetch(config.metadataFile);
    if (!response.ok) throw new Error('Falha ao carregar metadados');
    
    const data = await response.json();
    
    // Filtrar arquivos excluídos e adicionar ícones
    filesCache = data
      .filter(file => !config.excludedFiles.includes(file.name))
      .map(file => ({
        ...file,
        icon: getFileIcon(file.name),
        size: formatBytes(file.size),
        lastModified: formatDate(file.lastModified)
      }));
    
    renderFiles(filesCache);
  } catch (error) {
    console.error('Erro ao carregar metadados:', error);
    fileList.innerHTML = `
      <li class="error-message">
        Erro ao carregar arquivos. Por favor, tente recarregar a página.
      </li>
    `;
  }
};

// Inicialização
const init = () => {
  setupEventListeners();
  loadFilesMetadata();
};

document.addEventListener('DOMContentLoaded', init);