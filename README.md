<h1 align="center">Hi, I'm Vinayak Mangal 👋</h1>

<p align="center">
  <b>Quantitative modelling · Optimisation · Building things that are honest about what they show</b>
</p>

<p align="center">
  <img src="donut.svg" width="432" alt="Spinning ASCII donut">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/C-A8B9CC?style=flat-square&logo=c&logoColor=black" alt="C">
  <img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/OR--Tools-4285F4?style=flat-square&logo=google&logoColor=white" alt="OR-Tools">
  <img src="https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white" alt="NumPy">
</p>

---

I like problems where the maths has to survive contact with real data: calibrating option-pricing models on a decade of market prices, or getting a constraint solver to plan railway maintenance around a real timetable. I care as much about the evaluation as the model, so my projects ship with their benchmarks, their failure cases and the numbers behind every claim.

## 🔭 Featured projects

### 📈 [Double Heston 2.0 — NIFTY 50](https://github.com/mangalvinayak13-vin/Dheston)

Recalibration and walk-forward evaluation of the Double Heston option model on ten years of NIFTY 50 option prices (2016–2026).

- Merton jumps, an independent exact pricer (COS, Lewis, Monte Carlo) and a **PINN surrogate** that makes calibration **~8× faster**
- Strict out-of-sample design: settings chosen on 2016–2021, tested on 1,173 days of 2022–2026
- Next-day implied-vol surface error cut from **5.03 → 1.10 vol points** against the original recipe
- Every number traced to its source file, with the findings that *didn't* hold up written down too

`Python` `PyTorch` `quant finance` `stochastic volatility` `PINNs`

### 🚆 [SIH26027 — AI-Powered Automatic Block Planning](https://github.com/mangalvinayak13-vin/sih26027-block-planning)

Smart India Hackathon 2026 prototype: a decision-support tool for planning railway maintenance blocks.

- Cross-checks block requests from Engineering, S&T, TRD and Traffic against each other, the timetable and gang availability
- **Google OR-Tools CP-SAT** builds a ranked shortlist of feasible plans, with explanations for rejected requests
- Planner dashboard for approve/reject; the solver never confirms a block on its own

`Python` `OR-Tools` `React` `optimisation`

## 🌱 Right now

- Taking Double Heston 2.0 to the **Polarizer exhibition (Feb 2027)**
- Recording live NIFTY / BANKNIFTY option chains for out-of-sample testing
- Practising DSA on LeetCode

## 📊 Stats

<p align="center">
  <img height="160" src="https://github-readme-stats.vercel.app/api/top-langs/?username=mangalvinayak13-vin&layout=compact&hide_border=true" alt="Top languages">
</p>
