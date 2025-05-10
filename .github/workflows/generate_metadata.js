const fs = require('fs');
const path = require('path');
const { Octokit } = require('@octokit/rest');

// Configurações
const config = {
  owner: 'josieljluz',
  repo: 'josieljluz.github.io',
  branch: 'main',
  excludedFiles: ['index.html', '.gitignore', 'README.md', 'style.css', 'script.js', 'files_metadata.json'],
  outputFile: 'files_metadata.json'
};

// Autenticação
const octokit = new Octokit({
  auth: process.env.PAGES_GITHUB_TOKEN
});

async function getFileMetadata() {
  try {
    // Obter lista de arquivos
    const { data: files } = await octokit.repos.getContent({
      owner: config.owner,
      repo: config.repo,
      ref: config.branch
    });

    // Filtrar apenas arquivos (não diretórios) e excluir os não desejados
    const fileList = files.filter(item => 
      item.type === 'file' && !config.excludedFiles.includes(item.name)
    );

    // Obter metadados para cada arquivo
    const filesMetadata = await Promise.all(
      fileList.map(async file => {
        // Obter informações de commit mais recente
        const { data: commits } = await octokit.repos.listCommits({
          owner: config.owner,
          repo: config.repo,
          path: file.path,
          per_page: 1
        });

        return {
          name: file.name,
          path: file.path, // Caminho relativo para download
          size: file.size,
          lastModified: commits[0]?.commit?.committer?.date || new Date().toISOString(),
          download_url: file.download_url
        };
      })
    );

    // Salvar metadados em arquivo JSON
    fs.writeFileSync(
      path.join(__dirname, config.outputFile),
      JSON.stringify(filesMetadata, null, 2)
    );

    console.log(`Metadados gerados com sucesso em ${config.outputFile}`);
  } catch (error) {
    console.error('Erro ao gerar metadados:', error);
    process.exit(1);
  }
}

getFileMetadata();