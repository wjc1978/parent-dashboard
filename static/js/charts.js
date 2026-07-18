document.addEventListener("DOMContentLoaded", () => {
  const bpCtx = document.getElementById("bpChart");
  if (bpCtx) {
    const labels = JSON.parse(bpCtx.dataset.labels);
    const systolic = JSON.parse(bpCtx.dataset.systolic);
    const diastolic = JSON.parse(bpCtx.dataset.diastolic);

    new Chart(bpCtx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Systolic",
            data: systolic,
            borderColor: "#e0403d"
          },
          {
            label: "Diastolic",
            data: diastolic,
            borderColor: "#2f6fed"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }

  const sodiumCtx = document.getElementById("sodiumChart");
  if (sodiumCtx) {
    const labels = JSON.parse(sodiumCtx.dataset.labels);
    const amounts = JSON.parse(sodiumCtx.dataset.amounts);

    new Chart(sodiumCtx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Sodium (mg)",
            data: amounts,
            backgroundColor: "#f3a13a"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }
});
