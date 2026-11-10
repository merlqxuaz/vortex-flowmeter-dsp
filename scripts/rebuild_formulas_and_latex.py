import json
import os
import re

DATA_PATH = r"D:\ProjectTest\vortex-flowmeter-dsp\data\formulas.json"
forms = json.load(open(DATA_PATH, "r", encoding="utf-8"))

# Exact, high-fidelity LaTeX mapping for all formulas in the book
LATEX_MAP = {
    "1.2.1": r"\frac{h}{l} = 0.2806",
    "1.2.2": r"f = \frac{Sr \cdot v_1}{d}",
    "1.2.3": r"v_1 = \frac{v}{m}",
    "1.2.4": r"f = \frac{Sr \cdot v}{m \cdot d}",
    "1.2.5": r"q_v = \frac{\pi D^2}{4} v = \frac{\pi D^2 m d f}{4 Sr} = \frac{f}{K}",

    "2.1.1": r"x(n) = \frac{1}{a_0}\left[\sum_{i=0}^m b_i u(n-i) - \sum_{j=1}^k a_j x(n-j)\right]",
    "2.1.2": r"\delta_{xx}(k) = \frac{1}{N}|X(k)|^2",
    "2.1.3": r"X(k) = \sum_{n=0}^{N-1} x(n) W_N^{nk}, \quad k = 0, 1, \dots, N-1",
    "2.1.4": r"X(k) = \sum_{n=0}^{N/2-1} x_e(n) W_{N/2}^{nk} + W_N^k \sum_{n=0}^{N/2-1} x_o(n) W_{N/2}^{nk}",
    "2.1.5": r"g(n) = x_e(n) + j x_o(n), \quad n = 0, 1, \dots, N/2 - 1",
    "2.1.6": r"G(k) = X_e(k) + j X_o(k)",
    "2.1.7": r"G(N/2 - k) = X_e^*(k) - j X_o^*(k)",
    "2.1.8": r"X_e(k) = \frac{G(k) + G^*(N/2 - k)}{2}",
    "2.1.9": r"X_o(k) = \frac{G(k) - G^*(N/2 - k)}{2j}",
    "2.1.10": r"f_v = \frac{n \cdot f_s}{N_s}",
    "2.1.11": r"n = \frac{n Y(n) + (n+1) Y(n+1)}{Y(n) + Y(n+1)}",
    "2.1.12": r"f = \frac{n \cdot f_s}{N_s}",
    "2.1.13": r"x(t) = \sin(2\pi f_0 t) + 0.5 \sin(2\pi f_1 t)",

    "2.2.1": r"FR = \frac{3600 \cdot fre}{k}",
    "2.2.2": r"q_w = q_n \frac{P_n T_w}{P_w T_n}",
    "2.2.3": r"\rho_{ya} = \frac{1 + 0.424805 \sqrt{133-t} + 0.015938(133-t)}{4.2830 + 0.813055 \sqrt{133-t} - 0.008286(133-t)}",
    "2.2.4": r"TxPR = \frac{CLK}{FR} \times k - 1",
    "2.2.5": r"TxCMPR = 0.5 \times TxPR",

    "2.3.1": r"E_l = \frac{K_{\max} - K_{\min}}{K_{\max} + K_{\min}} \times 100\%",
    "2.3.2": r"E_r = \frac{1}{\bar{K}} \sqrt{\frac{\sum_{i=1}^n (K_i - \bar{K})^2}{n-1}} \times 100\%",

    "3.1.1": r"H(z^{-1}) = \frac{1 + \alpha z^{-1} + z^{-2}}{1 + \rho \alpha z^{-1} + \rho^2 z^{-2}}",
    "3.1.2": r"H(z^{-1}) = \frac{1 + \rho_1 \alpha z^{-1} + \rho_1^2 z^{-2}}{1 + \rho_2 \alpha z^{-1} + \rho_2^2 z^{-2}}",
    "3.1.3": r"\rho_1 = a + b\omega + c\omega^2",
    "3.1.4": r"\rho_2 = a + b\omega + c\omega^2",
    "3.1.5": r"|H(e^{j\omega_0})| = \frac{\sqrt{(1-2\rho_1+\rho_1^2)-4\rho_1(1-2\rho_1+\rho_1^2)\cos^2\omega_0}}{\sqrt{(1-2\rho_2+\rho_2^2)-4\rho_2(1-2\rho_2+\rho_2^2)\cos^2\omega_0}}",
    "3.1.6": r"|H(e^{j\omega_0})| \approx \frac{1 - \rho_1}{1 - \rho_2}",
    "3.1.7": r"|H(e^{j\omega_0})|^2 \approx \left(\frac{1 - \rho_1}{1 - \rho_2}\right)^2",
    "3.1.8": r"d = \frac{1 - \rho_1}{1 - \rho_2}",
    "3.1.9": r"H(z^{-1}) = \frac{1 + \rho_1 \alpha z^{-1} + \rho_1^2 z^{-2}}{1 + \rho_2 \alpha z^{-1} + \rho_2^2 z^{-2}}",
    "3.1.10": r"\alpha = -2\cos\omega_0",
    "3.1.11": r"\rho_2 = a + b\omega + c\omega^2",
    "3.1.12": r"d = \frac{1 - \rho_1}{1 - \rho_2}",
    "3.1.13": r"\omega_0 = \frac{2\pi f_0}{f_s}",
    "3.1.14": r"w = 1 / f_s",
    "3.1.15": r"y = y_s + y_n = a\sin(\omega t + \phi) + b\sin(\omega t) = (a\cos\phi + b)\sin(\omega t) + a\sin\phi\cos(\omega t)",
    "3.1.16": r"\cos\phi > -\frac{a}{2b}",
    "3.1.17": r"\cos\phi > -\frac{a}{2b} \ge -\frac{1}{2}",
    "3.1.18": r"\frac{2\pi}{3} \le \phi \le \frac{4\pi}{3}",
    "3.1.19": r"\Delta f = \frac{f_s}{N}",
    "3.1.20": r"f_s > 2 f_{\max}",
    "3.1.21": r"k' = \begin{cases} \frac{k y_k + (k+1)y_{k+1}}{y_k + y_{k+1}}, & y_{k-1} < y_{k+1} \\ \frac{k y_k + (k-1)y_{k-1}}{y_k + y_{k-1}}, & y_{k-1} \ge y_{k+1} \end{cases}",
    "3.1.22": r"f = \frac{k' f_s}{N}",
    "3.1.23": r"A = \frac{\Delta k \pi y_k}{\sin(\Delta k \pi)} = \frac{(k - k')\pi y_k}{\sin((k - k')\pi)}",

    "4.1.1": r"V_+ = 1.235 \times \frac{R_1 + R_2}{R_2} = 1.235 + 1.235 \times \frac{R_1}{R_2}",
    "4.1.2": r"V_- = \left[1.235 - \frac{R_1}{R_1 + R_2} V_{DD}\right] \times \frac{R_1 + R_2}{R_2}",
    "4.1.3": r"I_0 = \begin{cases} I_{sys}, & I_{sys} > 99 I_{in} \\ 100 I_{in}, & I_{sys} \le 99 I_{in} \end{cases}",
    "4.1.4": r"Y = a X + b",
    "4.1.5": r"X = \frac{Y - b}{a}",
    "4.1.6": r"\eta = \frac{V_0 \times I_0}{V_0 \times I_0 + V_i \times I_q}",
    "4.1.7": r"V_i \times I_i \times \eta = V_0 \times I_0",
    "4.1.8": r"I_0 = \frac{V_i \times I_i \times \eta}{V_0}",

    "4.2.1": r"f_s = N_s F_s",
    "4.3.1": r"f_0 = \frac{(k + d)f_s}{N}",
    "4.4.1": r"\frac{F_x}{N_x} = \frac{F_s}{N_s}",

    "5.2.1": r"y(r) = g(r) + j h(r)",
    "5.2.2": r"Y(k) = \sum_{r=0}^{N-1} [g(r) + j h(r)] e^{-j\frac{2\pi}{N}kr}",
    "5.2.3": r"G(k) = \frac{1}{2}[Y(k) + Y^*(N-k)]",
    "5.2.4": r"H(k) = \frac{1}{2j}[Y(k) - Y^*(N-k)]",
    "5.2.5": r"X(k)_{real} = G(k)_{real} + H(k)_{real}\cos\frac{2k\pi}{2048} + H(k)_{image}\sin\frac{2k\pi}{2048}",
    "5.2.6": r"X(k)_{image} = G(k)_{image} - H(k)_{real}\sin\frac{2k\pi}{2048} + H(k)_{image}\cos\frac{2k\pi}{2048}",
    "5.2.7": r"e(k) = d(k) - y(k) = d(k) - \mathbf{W}^T(k) \mathbf{X}(k)",
    "5.2.8": r"\mathbf{W}(k+1) = \mathbf{W}(k) + 2\mu e(k) \mathbf{X}(k)",
    "5.2.9": r"0 < \mu < \frac{1}{\lambda_{\max}}",
    "5.2.10": r"0 < \mu < \frac{1}{\text{tr}[\mathbf{R}]}",
    "5.2.11": r"\text{tr}[\mathbf{R}] = (L+1)\sigma_x^2",
    "5.2.12": r"0 < \mu < \frac{1}{(L+1)\sigma_x^2}",
    "5.2.13": r"E[\mathbf{W}(k)] = [\mathbf{I} - 2\mu\mathbf{R}]^k \mathbf{W}(0) + \mathbf{W}^*",

    "6.1.1": r"WT(a, \tau) = \frac{1}{\sqrt{a}} \int_{-\infty}^{+\infty} f(t) \psi^*\left(\frac{t-\tau}{a}\right) dt",
    "6.1.2": r"c_j(k) = \sum_{m} h(m-2k) c_{j-1}(m)",
    "6.1.3": r"d_j(k) = \sum_{m} g(m-2k) c_{j-1}(m)",
    "6.1.4": r"c_{j-1}(m) = \sum_{k} h(m-2k) c_j(k) + \sum_{k} g(m-2k) d_j(k)",
    "6.1.5": r"U_N = M \frac{dI}{dt}",

    "6.2.1": r"V_{HART} = V_{OUTP-P} \cdot \frac{C_{SLEW}}{C_{SLEW} + C_{HART}}",
    "6.2.2": r"\tau = R_{DAC} \cdot (C_{SLEW} + C_{HART})",

    "6.3.1": r"(E_r)_i = \frac{1}{\bar{K}_i}\sqrt{\frac{\sum_{j=1}^n (K_{ij} - \bar{K}_i)^2}{n-1}} \times 100\%",
    "6.3.2": r"E_r = \max\{(E_r)_i\}",

    "7.1.1": r"x_1(n) = s(n) + n_1(n)",
    "7.1.2": r"x_2(n) = \alpha s(n - M) + n_2(n)",
    "7.1.3": r"\hat{R}_{12}(m) = \frac{1}{N}\sum_{n=0}^{N-1-|m|} x_1(n) x_2(n+m)",
    "7.1.4": r"\bar{R}_{12}(m) = \alpha R_{ss}(m - M)",
    "7.1.5": r"R_{ss}(m) \le R_{ss}(0)",

    "7.2.1": r"\lambda = \frac{v}{f} = \frac{d}{Sr}",

    "7.3.1": r"\hat{R}_{12}(m) = \frac{1}{N}\sum_{n=0}^{N-1-|m|} x_1(n) x_2(n+m)",
    "7.3.2": r"\hat{R}_{12}(m) = \frac{1}{N-|m|}\sum_{n=0}^{N-1-|m|} x_1(n) x_2(n+m)",

    "7.4.1": r"x_1(n_j) = x_1(n), \quad n=0, s, 2s, \dots, N-s",
    "7.4.2": r"x_2(n_j) = x_2(n), \quad n=0, s, 2s, \dots, N-s",

    "7.6.1": r"Re = \frac{\rho v d}{\eta}",

    "8.1.1": r"V(t) = A(t)\sin\left(\omega_c t + k\int_0^t m(\lambda)d\lambda\right)",
    "8.1.2": r"P(k) = \frac{1}{K}\sum_{r=0}^{K-1} P_r(k)",
    "8.1.3": r"P_r(k) = \frac{1}{N}\left|\sum_{n=1}^N x(n) e^{-j\frac{2\pi}{N}kn}\right|^2",
    "8.1.4": r"f(x) = \frac{\alpha}{\sqrt{2\pi}\sigma_1} e^{-\frac{(x-\mu_1)^2}{2\sigma_1^2}} + \frac{1-\alpha}{\sqrt{2\pi}\sigma_2} e^{-\frac{(x-\mu_2)^2}{2\sigma_2^2}}",
    "8.1.5": r"\alpha(t) = A(t)\sin(\omega_c t + \phi(t))",
    "8.1.6": r"f(t) = \frac{1}{2\pi}\frac{d}{dt}[\omega_c t + \phi(t)] = f_c + \frac{1}{2\pi}\frac{d\phi(t)}{dt}",
    "8.1.7": r"y(t) = \delta(t)\sin\left(\omega_c t + k\int_0^t m(\lambda)d\lambda\right)",
    "8.1.8": r"y(t) = \delta(t)\sin\left(\omega_c t + k\int_0^t m(\lambda)d\lambda\right) + A_s\sin(\omega_s t) + A_p\sin(\omega_p t)",

    "8.2.1": r"Y = A X^2 + B X + C",
    "8.2.2": r"D = \frac{1}{N}\sum_{i=0}^{N-1} (f_i - \bar{f})^2",

    "9.2.1": r"Y = \begin{cases} A X^2 + B X + C, & a \le X \le b \\ \frac{2}{3} V_{\max}, & X > b \end{cases}",
    "9.2.2": r"D(f) = \frac{1}{N}\sum_{i=1}^N (f_i - \bar{f})^2",
    "9.2.3": r"V[i] = \begin{cases} \frac{n M[a] + M[b]}{n+1}, & i=2 \\ \frac{n V[i-1] + M[i]}{n+1}, & i > 2 \end{cases}",

    "10.2.1": r"A = \begin{cases} a f^2 + b f + c, & f_{\min} \le f < f_{sat} \\ \frac{1}{2}, & f \ge f_{sat} \end{cases}",
    "10.2.2": r"Var_{th} = \frac{1}{2}(Var_{\max} + Var_{\min})",
    "10.2.3": r"V_{1i} = |f_{a1} - f_{li}|, \quad i = 1, 2, \dots, m",
    "10.2.4": r"D_i(F_i) = \frac{1}{N}\sum_{j=1}^N (f_{ij} - \bar{f}_i)^2, \quad i = 1, 2, \dots, M",
    "10.2.5": r"d_c = \begin{cases} \max\{d_i\}, & i \le 5 \\ \bar{d}, & 5 < i < 15 \end{cases}",
    "10.2.6": r"R_j = \begin{cases} \bar{r}, & 2 \le i < 30 \\ \tilde{r}, & i \ge 30 \end{cases}",

    "11.2.1": r"x_0(t) = a_0 + b_0 e^{-\xi_0 t}\sin(2\pi f_0 t + \phi_0)",
    "11.2.2": r"x(t) = \sum_{i=1}^n x_i(t) + n_e(t)",
    "11.2.3": r"e_1 = \left|\frac{A_2 - A_1}{A_1}\right| \times 100\%",
    "11.2.4": r"\rho_{xy} = \frac{\text{cov}(x,y)}{\sqrt{\text{cov}(x,x)}\sqrt{\text{cov}(y,y)}}",
    "11.2.5": r"e_2 = \frac{1}{n}\sum_{i=1}^n (C_1(i) - C_2(i))^2",

    "11.3.1": r"X_{k+1} = A X_k + B U_k + G w_k",
    "11.3.2": r"Y_{k+1} = H X_{k+1} + D v_{k+1}",
    "11.3.3": r"E[w_k] = w, \quad \text{cov}[w_k] = Q \delta_{kj}",
    "11.3.4": r"E[v_k] = v, \quad \text{cov}[v_k] = R \delta_{kj}",
    "11.3.5": r"X_{k|k-1} = A X_{k-1|k-1} + B U_{k-1|k-1} + G w",
    "11.3.6": r"P_{k|k-1} = A P_{k-1|k-1} A^T + G Q G^T",
    "11.3.7": r"K_k = \frac{P_{k|k-1} H^T}{H P_{k|k-1} H^T + D R D^T}",
    "11.3.8": r"X_{k|k} = X_{k|k-1} + K_k(Y_k - H X_{k|k-1} - D v)",
    "11.3.9": r"P_{k|k} = (I - K_k H) P_{k|k-1}",
    "11.3.10": r"D = \frac{\max(PPV)}{\min(PPV)}",
    "11.3.11": r"Q = A V_{th}^2 + B V_{th} + C",
    "11.3.12": r"S^2 = \frac{1}{T-1}\sum_{t=1}^T (x_t - \bar{x})^2"
}

# Update all 128 formulas
updated_count = 0
for f in forms:
    num = f["num"]
    if num in LATEX_MAP:
        f["latex"] = LATEX_MAP[num]
        updated_count += 1
    else:
        # Fallback convert ocr_text to latex
        clean = f.get("ocr_text", "").replace(f"({num})", "").strip()
        f["latex"] = clean

print(f"Assigned exact LaTeX to {updated_count} / {len(forms)} formulas.")
with open(DATA_PATH, "w", encoding="utf-8") as out:
    json.dump(forms, out, ensure_ascii=False, indent=2)
print("Updated formulas.json successfully.")
