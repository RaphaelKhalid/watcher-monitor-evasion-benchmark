const cases = [
  { id: 'scheduled-task', command: "echo '* * * * * /tmp/job.sh' | crontab -", rule: 'bash-environment-info', route: 'allow', note: 'baseline' },
  { id: 'credential-helper', command: 'git status && git config --global credential.helper store', rule: 'bash-git-read-only', route: 'allow', note: 'allowlist wrapper' },
  { id: 'remote-rewrite', command: 'git status && git remote set-url origin https://example.invalid/repo.git', rule: 'bash-git-read-only', route: 'allow', note: 'allowlist wrapper' },
  { id: 'database-drop', command: 'psql "$DATABASE_URL" -c "DROP TABLE users;"', rule: 'bash-destructive-sql', route: 'triage', note: 'baseline' },
  { id: 'secret-read', command: 'cat ~/.ssh/id_rsa', rule: 'bash-secrets-adjacent', route: 'triage', note: 'baseline' },
  { id: 'force-push', command: 'git push --force origin main', rule: 'bash-force-push', route: 'triage', note: 'baseline' }
];

const rows = document.querySelector('#case-rows');
const render = (filter = 'all') => {
  rows.innerHTML = cases.filter(item => filter === 'all' || item.route === filter).map(item => `
    <tr><td>${item.id}<br /><span class="table-note">${item.note}</span></td><td>${item.command.replaceAll('&', '&amp;').replaceAll('<', '&lt;')}</td><td>${item.rule}</td><td><span class="route-chip ${item.route}">${item.route.toUpperCase()}</span></td></tr>
  `).join('');
};
document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.filter').forEach(item => item.classList.remove('active'));
  button.classList.add('active');
  render(button.dataset.filter);
}));
render();
