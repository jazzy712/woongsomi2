new Vue({
  el: '#spot-app',
  data: {
    // 기본값을 2023-01-01 ~ 2025-12-31 로 설정
    start_date: '2023-01-01',
    end_date:   '2025-12-31',
    chart:      null
  },
  mounted() {
    // 화면이 뜰 때 자동으로 금 가격 차트를 그려 줍니다
    this.loadData('gold');
  },
  methods: {
    loadData(metal) {
      // 날짜 포맷이 ISO (YYYY-MM-DD) 이므로 그대로 URL에 붙여도 됩니다
      const url = `/savings/spot/data/${metal}/?start_date=${this.start_date}&end_date=${this.end_date}`;
      fetch(url)
        .then(res => res.json())
        .then(data => {
          if (data.error) {
            return alert(data.error);
          }
          // 기존 차트가 있으면 파괴
          if (this.chart) this.chart.destroy();
          const ctx = document.getElementById('spotChart').getContext('2d');
          this.chart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: data.dates,
              datasets: [{
                label: metal === 'gold' ? '금 가격 (USD/oz)' : '은 가격 (USD/oz)',
                data: data.prices,
                borderColor: metal === 'gold' ? '#f39c12' : '#7f8c8d',
                backgroundColor: metal === 'gold'
                  ? 'rgba(243, 156, 18, 0.1)'
                  : 'rgba(127, 140, 141, 0.1)',
                fill: true,
                tension: 0.2,
              }]
            },
            options: {
              responsive: true,
              scales: {
                x: {
                  display: true,
                  title: {
                    display: true,
                    text: '날짜'
                  }
                },
                y: {
                  display: true,
                  title: {
                    display: true,
                    text: metal === 'gold' ? '금 가격 (USD/oz)' : '은 가격 (USD/oz)'
                  },
                  beginAtZero: false
                }
              }
            }
          });
        })
        .catch(err => {
          console.error(err);
          alert('데이터를 불러오는 중 오류가 발생했습니다.');
        });
    }
  }
});
