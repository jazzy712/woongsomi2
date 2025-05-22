new Vue({
  el: '#spot-app',
  data: {
    start_date: '',
    end_date: '',
    chart: null
  },
  methods: {
    loadData(metal) {
      let url = `/savings/spot/data/${metal}/?start_date=${this.start_date}&end_date=${this.end_date}`;
      fetch(url)
        .then(res => res.json())
        .then(data => {
          if (this.chart) this.chart.destroy();
          const ctx = document.getElementById('spotChart').getContext('2d');
          this.chart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: data.dates,
              datasets: [{
                label: metal === 'gold' ? '금 가격' : '은 가격',
                data: data.prices,
                borderColor: '#f39c12',
                backgroundColor: 'rgba(243, 156, 18, 0.1)',
              }]
            }
          });
        });
    }
  }
});
