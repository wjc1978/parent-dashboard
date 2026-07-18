document.addEventListener("DOMContentLoaded", () => {
  const ctx = document.getElementById("bpChart");
  if (!ctx) return;

  const labels = JSON.parse(ctx.dataset.labels);
  const systolic = JSON.parse(ctx.dataset.systolic);
  const diastolic = JSON.parse(ctx.dataset.diastolic);

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Systolic",
          data: systolic,
          borderColor: "red"
        },
        {
          label: "Diastolic",
          data: diastolic,
          borderColor: "blue"
        }
      ]
    }
  });
});
