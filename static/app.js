const regionSelect = document.getElementById('regionSelect');
const statAvgScore = document.getElementById('statAvgScore');
const statDropout = document.getElementById('statDropout');
const statSchools = document.getElementById('statSchools');
const statStudents = document.getElementById('statStudents');
const statTeachers = document.getElementById('statTeachers');
const statInternet = document.getElementById('statInternet');
const statSTR = document.getElementById('statSTR');
const recsList = document.getElementById('recsList');

const predictForm = document.getElementById('predictForm');
const pSchools = document.getElementById('p_schools');
const pInternet = document.getElementById('p_internet');
const pTeachers = document.getElementById('p_teachers');
const pStudents = document.getElementById('p_students');
const predictResult = document.getElementById('predictResult');

const sentText = document.getElementById('sentText');
const sentBtn = document.getElementById('sentBtn');
const sentResult = document.getElementById('sentResult');

let compareChart;

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

async function loadRegions() {
  const data = await fetchJSON('/api/regions');
  regionSelect.innerHTML = '';
  for (const r of data.regions) {
    const opt = document.createElement('option');
    opt.value = r; opt.textContent = r; regionSelect.appendChild(opt);
  }
  if (data.regions.length > 0) {
    regionSelect.value = data.regions[0];
    onRegionChange();
  }
}

async function onRegionChange() {
  const region = regionSelect.value;
  const stats = await fetchJSON(`/api/stats?region=${encodeURIComponent(region)}`);
  statAvgScore.textContent = Number(stats.avg_score).toFixed(1);
  statDropout.textContent = Number(stats.dropout_rate).toFixed(1);
  statSchools.textContent = stats.schools.toLocaleString();
  statStudents.textContent = stats.students.toLocaleString();
  statTeachers.textContent = stats.teachers.toLocaleString();
  statInternet.textContent = Number(stats.internet_coverage).toFixed(0);
  statSTR.textContent = Number(stats.student_teacher_ratio).toFixed(1);

  // Recommendations
  const recs = await fetchJSON(`/api/recommendations?region=${encodeURIComponent(region)}`);
  recsList.innerHTML = '';
  for (const item of recs.recommendations) {
    const li = document.createElement('li');
    li.textContent = item; recsList.appendChild(li);
  }
  if (recs.peer_regions?.length) {
    const li = document.createElement('li');
    li.textContent = `O‘xshash hududlar (cluster): ${recs.peer_regions.join(', ')}`;
    recsList.appendChild(li);
  }
}

async function buildCompareChart() {
  const cmp = await fetchJSON('/api/compare?metric=avg_score');
  const labels = cmp.data.map((d) => d.region);
  const values = cmp.data.map((d) => d[cmp.metric]);

  const ctx = document.getElementById('compareChart').getContext('2d');
  if (compareChart) compareChart.destroy();
  compareChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'O‘rtacha ball',
        data: values,
        backgroundColor: '#38bdf8',
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: false } }
    }
  });
}

predictForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const schools = Number(pSchools.value);
  const internet = Number(pInternet.value);
  const teachers = Number(pTeachers.value);
  const students = Number(pStudents.value);
  const str = students / teachers;
  const sps = students / schools;
  const tps = teachers / schools;

  try {
    const resp = await fetchJSON('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        schools,
        internet_coverage: internet,
        teachers,
        students,
        student_teacher_ratio: str,
        students_per_school: sps,
        teachers_per_school: tps
      })
    });
    predictResult.textContent = `Bashorat — O‘rtacha ball: ${resp.predicted_avg_score.toFixed(1)}, Drop-out: ${resp.predicted_dropout_rate.toFixed(1)}%`;
  } catch (err) {
    predictResult.textContent = 'Xatolik: ' + err.message;
  }
});

sentBtn.addEventListener('click', async () => {
  const text = sentText.value.trim();
  if (!text) return;
  try {
    const resp = await fetchJSON('/api/sentiment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const s = resp.scores;
    sentResult.textContent = `Natija: ${resp.label} (compound: ${s.compound.toFixed(3)})`;
  } catch (err) {
    sentResult.textContent = 'Xatolik: ' + err.message;
  }
});

regionSelect.addEventListener('change', onRegionChange);

(async function init() {
  try {
    await loadRegions();
    await buildCompareChart();
  } catch (err) {
    console.error(err);
  }
})();