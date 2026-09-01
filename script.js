/* =====================================================
   API
===================================================== */

const API = "https://reviewpay.onrender.com";


let allRiskTransactions = [];

let currentRiskFilter = "All";


/* =====================================================
   CHART COLORS
===================================================== */

const CHART_COLORS = [
    "#2563eb",
    "#7c3aed",
    "#06b6d4",
    "#16a34a",
    "#f59e0b",
    "#dc2626",
    "#db2777"
];


/* =====================================================
   UTILITY
===================================================== */

function formatCurrency(amount) {

    return "₹" +
        Number(amount || 0)
            .toLocaleString("en-IN");
}


function formatFailureReason(reason) {

    if (!reason) {
        return "-";
    }

    return String(reason)
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            letter =>
                letter.toUpperCase()
        );
}


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =====================================================
   NOTIFICATION
===================================================== */

function showNotification(message) {

    const notification =
        document.getElementById(
            "notification"
        );

    if (!notification) {
        return;
    }

    notification.innerText =
        message;

    notification.style.display =
        "block";

    setTimeout(() => {

        notification.style.display =
            "none";

    }, 3500);
}


/* =====================================================
   NAVIGATION
===================================================== */

function showSection(sectionId) {

    const sections =
        document.querySelectorAll(
            ".app-section"
        );

    const links =
        document.querySelectorAll(
            ".nav-link[data-section]"
        );


    sections.forEach(section => {

        section.classList.remove(
            "active-section"
        );

    });


    links.forEach(link => {

        link.classList.remove(
            "active"
        );

    });


    const target =
        document.getElementById(
            sectionId
        );


    const activeLink =
        document.querySelector(
            `.nav-link[data-section="${sectionId}"]`
        );


    if (target) {

        target.classList.add(
            "active-section"
        );

    }


    if (activeLink) {

        activeLink.classList.add(
            "active"
        );

    }


    if (
        sectionId ===
        "dashboard-section"
    ) {

        loadDashboard();

    }


    if (
        sectionId ===
        "risk-section"
    ) {

        loadRiskTransactions();

    }


    if (
        sectionId ===
        "analytics-section"
    ) {

        loadRiskTransactions();

    }


    if (
        sectionId ===
        "audit-section"
    ) {

        loadAuditLog();

    }
}


function setupNavigation() {

    const links =
        document.querySelectorAll(
            ".nav-link[data-section]"
        );


    links.forEach(link => {

        link.addEventListener(
            "click",
            event => {

                event.preventDefault();

                const sectionId =
                    link.dataset.section;

                showSection(
                    sectionId
                );

                history.replaceState(
                    null,
                    "",
                    `#${sectionId}`
                );

            }
        );

    });

}


/* =====================================================
   SUMMARY
===================================================== */

async function loadSummary() {

    try {

        const response =
            await fetch(
                `${API}/recovery-summary`
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load summary"
            );

        }


        const data =
            await response.json();


        const revenueRisk =
            document.getElementById(
                "revenueRisk"
            );


        if (revenueRisk) {

            revenueRisk.innerText =
                formatCurrency(
                    data.revenue_at_risk
                );

        }


        const revenueRecovered =
            document.getElementById(
                "revenueRecovered"
            );


        if (revenueRecovered) {

            revenueRecovered.innerText =
                formatCurrency(
                    data.total_recovered
                );

        }


        const recoveryRate =
            document.getElementById(
                "recoveryRate"
            );


        if (recoveryRate) {

            recoveryRate.innerText =
                `${data.recovery_rate}%`;

        }


        const successfulRecoveries =
            document.getElementById(
                "successfulRecoveries"
            );


        if (successfulRecoveries) {

            successfulRecoveries.innerText =
                data.successful_recoveries;

        }

    }
    catch (error) {

        console.error(error);

        showNotification(
            "Unable to load recovery summary"
        );

    }

}


/* =====================================================
   LOAD RISK TRANSACTIONS
===================================================== */

async function loadRiskTransactions() {

    try {

        const response =
            await fetch(
                `${API}/at-risk`
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load transactions"
            );

        }


        const data =
            await response.json();


        allRiskTransactions =
            Array.isArray(data)
                ? data
                : [];


        updatePriorityCards(
            allRiskTransactions
        );


        renderRiskTransactions(
            allRiskTransactions
        );


        renderAnalytics(
            allRiskTransactions
        );

    }
    catch (error) {

        console.error(error);


        const table =
            document.getElementById(
                "riskTable"
            );


        if (table) {

            table.innerHTML = `

                <tr>

                    <td
                        colspan="8"
                        class="loading"
                    >
                        Failed to load transactions.
                    </td>

                </tr>

            `;

        }


        showNotification(
            "Unable to load at-risk transactions"
        );

    }

}


/* =====================================================
   PRIORITY CARDS
===================================================== */

function updatePriorityCards(data) {

    const high =
        data.filter(
            transaction =>
                transaction.risk_level ===
                "High"
        ).length;


    const medium =
        data.filter(
            transaction =>
                transaction.risk_level ===
                "Medium"
        ).length;


    const low =
        data.filter(
            transaction =>
                transaction.risk_level ===
                "Low"
        ).length;


    const total =
        data.length;


    const safeTotal =
        total || 1;


    const highPercent =
        Math.round(
            (high / safeTotal) * 100
        );


    const mediumPercent =
        Math.round(
            (medium / safeTotal) * 100
        );


    const lowPercent =
        Math.max(
            0,
            100 -
            highPercent -
            mediumPercent
        );


    const values = {

        highCount:
            document.getElementById(
                "highRiskCount"
            ),

        mediumCount:
            document.getElementById(
                "mediumRiskCount"
            ),

        lowCount:
            document.getElementById(
                "lowRiskCount"
            ),

        highPercent:
            document.getElementById(
                "highRiskPercent"
            ),

        mediumPercent:
            document.getElementById(
                "mediumRiskPercent"
            ),

        lowPercent:
            document.getElementById(
                "lowRiskPercent"
            ),

        total:
            document.getElementById(
                "priorityTotal"
            ),

        highProgress:
            document.getElementById(
                "highProgress"
            ),

        mediumProgress:
            document.getElementById(
                "mediumProgress"
            ),

        lowProgress:
            document.getElementById(
                "lowProgress"
            ),

        riskCount:
            document.getElementById(
                "riskCount"
            )

    };


    if (values.highCount) {

        values.highCount.innerText =
            high;

    }


    if (values.mediumCount) {

        values.mediumCount.innerText =
            medium;

    }


    if (values.lowCount) {

        values.lowCount.innerText =
            low;

    }


    if (values.highPercent) {

        values.highPercent.innerText =
            `${highPercent}%`;

    }


    if (values.mediumPercent) {

        values.mediumPercent.innerText =
            `${mediumPercent}%`;

    }


    if (values.lowPercent) {

        values.lowPercent.innerText =
            `${lowPercent}%`;

    }


    if (values.total) {

        values.total.innerText =
            total;

    }


    if (values.highProgress) {

        values.highProgress.style.width =
            `${highPercent}%`;

    }


    if (values.mediumProgress) {

        values.mediumProgress.style.width =
            `${mediumPercent}%`;

    }


    if (values.lowProgress) {

        values.lowProgress.style.width =
            `${lowPercent}%`;

    }


    if (values.riskCount) {

        values.riskCount.innerText =
            total;

    }

}


/* =====================================================
   RISK FILTER
===================================================== */

function setRiskFilter(filter) {

    currentRiskFilter =
        filter;


    document
        .querySelectorAll(
            ".filter-btn"
        )
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.riskFilter ===
                filter
            );

        });


    applyTransactionFilters();

}


function goToRiskFilter(filter) {

    showSection(
        "risk-section"
    );


    setRiskFilter(
        filter
    );

}


/* =====================================================
   SEARCH
===================================================== */

function applyTransactionFilters() {

    const searchElement =
        document.getElementById(
            "transactionSearch"
        );


    const search =
        searchElement
            ?.value
            ?.trim()
            ?.toLowerCase() ||
        "";


    const filtered =
        allRiskTransactions.filter(
            transaction => {

                const matchesRisk =
                    currentRiskFilter ===
                    "All" ||
                    transaction.risk_level ===
                    currentRiskFilter;


                const transactionId =
                    String(
                        transaction.transaction_id
                    )
                    .toLowerCase();


                const matchesSearch =
                    !search ||
                    transactionId.includes(
                        search
                    );


                return (
                    matchesRisk &&
                    matchesSearch
                );

            }
        );


    renderRiskTransactions(
        filtered
    );

}


/* =====================================================
   RENDER RISK TABLE
===================================================== */

function renderRiskTransactions(data) {

    const table =
        document.getElementById(
            "riskTable"
        );


    const count =
        document.getElementById(
            "riskCount"
        );


    if (!table) {
        return;
    }


    if (count) {

        count.innerText =
            data.length;

    }


    if (data.length === 0) {

        table.innerHTML = `

            <tr>

                <td
                    colspan="8"
                    class="loading"
                >
                    No transactions match
                    the selected filter.
                </td>

            </tr>

        `;

        return;

    }


    table.innerHTML = "";


    data.forEach(transaction => {

        const riskLevel =
            transaction.risk_level;


        const riskClass =
            riskLevel === "High"
                ? "risk-high"
                : riskLevel === "Medium"
                    ? "risk-medium"
                    : "risk-low";


        const action =
            getActionText(
                transaction
            );


        const id =
            escapeHtml(
                transaction.transaction_id
            );


        const row =
            document.createElement(
                "tr"
            );


        row.innerHTML = `

            <td>

                <span class="transaction-id">
                    ${id}
                </span>

            </td>


            <td>

                <span class="amount">
                    ${formatCurrency(
                        transaction.amount
                    )}
                </span>

            </td>


            <td>

                ${escapeHtml(
                    formatFailureReason(
                        transaction.failure_reason
                    )
                )}

            </td>


            <td>

                ${escapeHtml(
                    transaction.payment_method ||
                    "-"
                )}

            </td>


            <td>

                ${escapeHtml(
                    transaction.attempt_count
                )}

            </td>


            <td>

                <span class="${riskClass}">

                    ${escapeHtml(
                        riskLevel
                    )}

                    (${escapeHtml(
                        transaction.risk_score
                    )})

                </span>

            </td>


            <td>

                <span class="action-text">

                    ${escapeHtml(
                        action
                    )}

                </span>

            </td>


            <td>

                <button
                    class="diagnose-btn"
                    onclick="diagnose('${id}')"
                >
                    Diagnose
                </button>


                <button
                    class="recover-btn"
                    onclick="recover('${id}')"
                >
                    Recover
                </button>

            </td>

        `;


        table.appendChild(
            row
        );

    });

}


/* =====================================================
   AI ACTION
===================================================== */

function getActionText(transaction) {

    const reason =
        transaction.failure_reason;


    if (
        reason === "timeout"
    ) {

        return "Retry Payment";

    }


    if (
        reason === "network_error"
    ) {

        return "Retry Payment";

    }


    if (
        reason === "insufficient_funds"
    ) {

        return "Payment Reminder";

    }


    if (
        reason === "bank_error"
    ) {

        if (
            Number(
                transaction.attempt_count
            ) >= 3
        ) {

            return "Escalate";

        }


        return "Retry Payment";

    }


    return "Review";

}


/* =====================================================
   ANALYTICS DATA
===================================================== */

function getActionAnalytics(data) {

    const counts = {};


    data.forEach(transaction => {

        const action =
            getActionText(
                transaction
            );


        counts[action] =
            (
                counts[action] ||
                0
            ) + 1;

    });


    return counts;

}


function getCauseAnalytics(data) {

    const counts = {};


    data.forEach(transaction => {

        const cause =
            formatFailureReason(
                transaction.failure_reason
            );


        counts[cause] =
            (
                counts[cause] ||
                0
            ) + 1;

    });


    return counts;

}


/* =====================================================
   BAR CHART
===================================================== */

function drawBarChart(
    svgId,
    data
) {

    const svg =
        document.getElementById(
            svgId
        );


    if (!svg) {
        return;
    }


    const entries =
        Object.entries(data)
            .sort(
                (a, b) =>
                    b[1] - a[1]
            );


    if (
        entries.length === 0
    ) {

        svg.innerHTML = `

            <text
                x="50%"
                y="50%"
                text-anchor="middle"
                class="chart-label"
            >
                No data available
            </text>

        `;

        return;

    }


    const width =
        svg.viewBox.baseVal.width ||
        520;


    const height =
        svg.viewBox.baseVal.height ||
        250;


    const margin = {

        top: 25,

        right: 20,

        bottom: 55,

        left: 42

    };


    const chartWidth =
        width -
        margin.left -
        margin.right;


    const chartHeight =
        height -
        margin.top -
        margin.bottom;


    const maxValue =
        Math.max(
            ...entries.map(
                item => item[1]
            )
        );


    let html = "";


    /* GRID */

    for (
        let i = 0;
        i <= 4;
        i++
    ) {

        const y =
            margin.top +
            chartHeight -
            (
                chartHeight *
                i /
                4
            );


        const value =
            Math.round(
                maxValue *
                i /
                4
            );


        html += `

            <line
                x1="${margin.left}"
                y1="${y}"
                x2="${width - margin.right}"
                y2="${y}"
                class="chart-grid-line"
            />

            <text
                x="${margin.left - 8}"
                y="${y + 4}"
                text-anchor="end"
                class="chart-label"
            >
                ${value}
            </text>

        `;

    }


    const slot =
        chartWidth /
        entries.length;


    const barWidth =
        Math.min(
            65,
            slot * .55
        );


    entries.forEach(
        ([label, value], index) => {

            const barHeight =
                maxValue > 0
                    ? (
                        value /
                        maxValue
                    ) *
                    chartHeight
                    : 0;


            const x =
                margin.left +
                (
                    slot *
                    index
                ) +
                (
                    slot -
                    barWidth
                ) / 2;


            const y =
                margin.top +
                chartHeight -
                barHeight;


            const shortLabel =
                label.length > 13
                    ? label.substring(
                        0,
                        11
                    ) + "..."
                    : label;


            html += `

                <rect
                    x="${x}"
                    y="${y}"
                    width="${barWidth}"
                    height="${barHeight}"
                    class="chart-bar"
                />

                <text
                    x="${x + barWidth / 2}"
                    y="${y - 7}"
                    text-anchor="middle"
                    class="chart-value"
                >
                    ${value}
                </text>

                <text
                    x="${x + barWidth / 2}"
                    y="${height - 25}"
                    text-anchor="middle"
                    class="chart-label"
                >
                    ${escapeHtml(
                        shortLabel
                    )}
                </text>

            `;

        }
    );


    html += `

        <line
            x1="${margin.left}"
            y1="${margin.top + chartHeight}"
            x2="${width - margin.right}"
            y2="${margin.top + chartHeight}"
            class="chart-axis"
        />

    `;


    svg.innerHTML =
        html;

}


/* =====================================================
   DONUT CHART
===================================================== */

function polarToCartesian(
    cx,
    cy,
    radius,
    angle
) {

    const radians =
        (
            angle -
            90
        ) *
        Math.PI /
        180;


    return {

        x:
            cx +
            radius *
            Math.cos(
                radians
            ),

        y:
            cy +
            radius *
            Math.sin(
                radians
            )

    };

}


function describeArc(
    cx,
    cy,
    radius,
    startAngle,
    endAngle
) {

    const start =
        polarToCartesian(
            cx,
            cy,
            radius,
            endAngle
        );


    const end =
        polarToCartesian(
            cx,
            cy,
            radius,
            startAngle
        );


    const largeArcFlag =
        endAngle -
        startAngle <= 180
            ? "0"
            : "1";


    return [

        "M",
        start.x,
        start.y,

        "A",
        radius,
        radius,
        0,
        largeArcFlag,
        0,
        end.x,
        end.y

    ].join(" ");

}


function drawDonutChart(
    svgId,
    legendId,
    data
) {

    const svg =
        document.getElementById(
            svgId
        );


    const legend =
        document.getElementById(
            legendId
        );


    if (!svg) {
        return;
    }


    const entries =
        Object.entries(data)
            .sort(
                (a, b) =>
                    b[1] - a[1]
            );


    if (
        entries.length === 0
    ) {

        svg.innerHTML = "";

        if (legend) {
            legend.innerHTML =
                "No data available";
        }

        return;

    }


    const total =
        entries.reduce(
            (
                sum,
                item
            ) =>
                sum + item[1],
            0
        );


    const cx = 110;

    const cy = 110;

    const radius = 75;


    let currentAngle = 0;


    let html = "";


    entries.forEach(
        ([label, value], index) => {

            const angle =
                (
                    value /
                    total
                ) *
                360;


            const start =
                currentAngle;


            const end =
                currentAngle +
                angle;


            const path =
                describeArc(
                    cx,
                    cy,
                    radius,
                    start,
                    end
                );


            const color =
                CHART_COLORS[
                    index %
                    CHART_COLORS.length
                ];


            html += `

                <path
                    d="${path}"
                    fill="none"
                    stroke="${color}"
                    stroke-width="30"
                    class="donut-segment"
                />

            `;


            currentAngle =
                end;

        }
    );


    html += `

        <circle
            cx="${cx}"
            cy="${cy}"
            r="51"
            fill="white"
        />

        <text
            x="${cx}"
            y="${cy - 2}"
            text-anchor="middle"
            class="donut-center-number"
        >
            ${total}
        </text>

        <text
            x="${cx}"
            y="${cy + 15}"
            text-anchor="middle"
            class="donut-center-label"
        >
            Payments
        </text>

    `;


    svg.innerHTML =
        html;


    if (legend) {

        legend.innerHTML =
            entries
                .map(
                    (
                        [label, value],
                        index
                    ) => {

                        const color =
                            CHART_COLORS[
                                index %
                                CHART_COLORS.length
                            ];


                        const percent =
                            Math.round(
                                (
                                    value /
                                    total
                                ) *
                                100
                            );


                        return `

                            <div class="legend-item">

                                <span
                                    class="legend-dot"
                                    style="
                                        background:${color}
                                    "
                                ></span>

                                <span>
                                    ${escapeHtml(
                                        label
                                    )}
                                </span>

                                <span class="legend-value">
                                    ${percent}%
                                </span>

                            </div>

                        `;

                    }
                )
                .join("");

    }

}


/* =====================================================
   RENDER ANALYTICS
===================================================== */

function renderAnalytics(data) {

    const actionData =
        getActionAnalytics(
            data
        );


    const causeData =
        getCauseAnalytics(
            data
        );


    drawBarChart(
        "actionBarChart",
        actionData
    );


    drawBarChart(
        "pageActionChart",
        actionData
    );


    drawDonutChart(
        "causeDonutChart",
        "causeLegend",
        causeData
    );


    drawDonutChart(
        "pageCauseChart",
        "pageCauseLegend",
        causeData
    );

}


/* =====================================================
   AI DIAGNOSIS
===================================================== */

async function diagnose(
    transactionId
) {

    try {

        showNotification(
            "AI is diagnosing the payment..."
        );


        const response =
            await fetch(
                `${API}/diagnose/${transactionId}`
            );


        const data =
            await response.json();


        if (data.error) {

            showNotification(
                data.error
            );

            return;

        }


        const transaction =
            data.transaction;


        const decision =
            data.ai_decision;


        document.getElementById(
            "decisionPanel"
        ).innerHTML = `

            <div class="decision-content">

                <div class="decision-grid">


                    <div class="decision-box">

                        <span>
                            Transaction
                        </span>

                        <strong>
                            ${escapeHtml(
                                transaction.transaction_id
                            )}
                        </strong>

                    </div>


                    <div class="decision-box">

                        <span>
                            Amount
                        </span>

                        <strong>
                            ${formatCurrency(
                                transaction.amount
                            )}
                        </strong>

                    </div>


                    <div class="decision-box">

                        <span>
                            Risk Score
                        </span>

                        <strong>
                            ${escapeHtml(
                                transaction.risk_score
                            )}
                        </strong>

                    </div>


                    <div class="decision-box">

                        <span>
                            Recovery Probability
                        </span>

                        <strong>
                            ${escapeHtml(
                                decision.recovery_probability
                            )}%
                        </strong>

                    </div>

                </div>


                <div class="ai-reason">

                    <strong>
                        🧠 AI Analysis
                    </strong>

                    <p>
                        ${escapeHtml(
                            decision.diagnosis
                        )}
                    </p>

                </div>


                <div class="ai-reason">

                    <strong>
                        🤖 Recommendation
                    </strong>

                    <p>

                        <b>
                            Recommended Action:
                        </b>

                        ${escapeHtml(
                            formatFailureReason(
                                decision.recommended_action
                            )
                        )}

                        <br><br>

                        ${escapeHtml(
                            decision.reason
                        )}

                    </p>

                </div>


                <div class="ai-reason">

                    <strong>
                        🛡 Safety
                    </strong>

                    <p>
                        Recovery is executed only
                        through the bounded recovery
                        engine with retry limits and
                        duplicate protection.
                    </p>

                </div>


                <div
                    style="
                        margin-top:15px;
                    "
                >

                    <button
                        class="recover-btn"
                        onclick="recover('${escapeHtml(
                            transaction.transaction_id
                        )}')"
                    >
                        Execute Safe Recovery
                    </button>

                </div>

            </div>

        `;


        showSection(
            "recovery-section"
        );

    }
    catch (error) {

        console.error(error);

        showNotification(
            "AI diagnosis failed"
        );

    }

}


/* =====================================================
   SINGLE RECOVERY
===================================================== */

async function recover(
    transactionId
) {

    try {

        showNotification(
            "Executing recovery action..."
        );


        const response =
            await fetch(
                `${API}/recover/${transactionId}`,
                {
                    method: "POST"
                }
            );


        const data =
            await response.json();


        if (data.error) {

            showNotification(
                data.error
            );

            return;

        }


        const result =
            data.recovery_result;


        let message =
            result.message;


        if (
            result.result ===
            "success"
        ) {

            message =
                `Payment recovered! ${
                    formatCurrency(
                        result.recovered_amount
                    )
                }`;

        }


        showNotification(
            message
        );


        await loadDashboard();


        document.getElementById(
            "decisionPanel"
        ).innerHTML = `

            <div class="decision-content">

                <div class="ai-reason">

                    <strong>
                        Recovery Result
                    </strong>

                    <p>
                        ${escapeHtml(
                            result.message
                        )}
                    </p>


                    <p>

                        <strong>
                            Action:
                        </strong>

                        ${escapeHtml(
                            formatFailureReason(
                                result.action
                            )
                        )}

                    </p>


                    <p>

                        <strong>
                            Result:
                        </strong>

                        ${escapeHtml(
                            formatFailureReason(
                                result.result
                            )
                        )}

                    </p>


                    <p>

                        <strong>
                            Recovered Amount:
                        </strong>

                        ${formatCurrency(
                            result.recovered_amount
                        )}

                    </p>


                    <p>

                        <strong>
                            Attempt Number:
                        </strong>

                        ${
                            result.attempt_number ||
                            "-"
                        }

                    </p>

                </div>

            </div>

        `;

    }
    catch (error) {

        console.error(error);

        showNotification(
            "Recovery request failed"
        );

    }

}


/* =====================================================
   BATCH RECOVERY
===================================================== */

async function runBatchRecovery() {

    const button =
        document.querySelector(
            ".recover-all-btn"
        );


    if (!button) {
        return;
    }


    button.disabled =
        true;


    button.innerText =
        "Processing...";


    showNotification(
        "AI batch recovery started..."
    );


    try {

        const response =
            await fetch(
                `${API}/recover-batch`,
                {
                    method: "POST"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                "Batch recovery failed"
            );

        }


        showNotification(
            `Batch complete: ${
                data.successful_recoveries
            } payments recovered`
        );


        await loadDashboard();


        document.getElementById(
            "decisionPanel"
        ).innerHTML = `

            <div class="decision-content">

                <div class="decision-grid">


                    <div class="decision-box">

                        <span>
                            Total Transactions
                        </span>

                        <strong>
                            ${data.total_transactions}
                        </strong>

                    </div>


                    <div class="decision-box">

                        <span>
                            Failed Transactions
                        </span>

                        <strong>
                            ${data.failed_transactions}
                        </strong>

                    </div>


                    <div class="decision-box">

                        <span>
                            Revenue At Risk
                        </span>

                        <strong>
                            ${formatCurrency(
                                data.revenue_at_risk
                            )}
                        </strong>

                    </div>


                    <div class="decision-box">

                        <span>
                            Recovery Rate
                        </span>

                        <strong>
                            ${data.recovery_rate}%
                        </strong>

                    </div>

                </div>


                <div class="ai-reason">

                    <strong>
                        Batch Recovery Completed
                    </strong>

                    <p>
                        Revenue Recovered:
                        ${formatCurrency(
                            data.revenue_recovered
                        )}
                    </p>

                    <p>
                        Successful Recoveries:
                        ${data.successful_recoveries}
                    </p>

                    <p>
                        Escalated Cases:
                        ${data.escalated_cases}
                    </p>

                    <p>
                        Skipped Already Recovered:
                        ${data.skipped_already_recovered}
                    </p>

                </div>

            </div>

        `;

    }
    catch (error) {

        console.error(error);

        showNotification(
            "Batch recovery failed"
        );

    }


    button.disabled =
        false;


    button.innerText =
        "Run AI Recovery";

}


/* =====================================================
   AUDIT LOG
===================================================== */

async function loadAuditLog() {

    try {

        const response =
            await fetch(
                `${API}/audit-log`
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load audit log"
            );

        }


        const data =
            await response.json();


        const table =
            document.getElementById(
                "auditTable"
            );


        if (!table) {
            return;
        }


        if (
            !data ||
            data.length === 0
        ) {

            table.innerHTML = `

                <tr>

                    <td
                        colspan="8"
                        class="loading"
                    >
                        No recovery actions yet.
                    </td>

                </tr>

            `;

            return;

        }


        table.innerHTML = "";


        data.forEach(log => {

            let resultClass =
                "audit-result";


            if (
                log.result ===
                "success"
            ) {

                resultClass =
                    "audit-success";

            }
            else if (
                log.result ===
                "failed" ||
                log.result ===
                "stopped"
            ) {

                resultClass =
                    "audit-failed";

            }
            else if (
                log.result ===
                "escalated"
            ) {

                resultClass =
                    "audit-warning";

            }


            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>

                    ${formatAuditTime(
                        log.timestamp
                    )}

                </td>


                <td>

                    <span class="transaction-id">

                        ${escapeHtml(
                            log.transaction_id
                        )}

                    </span>

                </td>


                <td>

                    ${formatCurrency(
                        log.amount
                    )}

                </td>


                <td>

                    ${escapeHtml(
                        formatFailureReason(
                            log.action
                        )
                    )}

                </td>


                <td>

                    ${
                        log.attempt_number ||
                        "-"
                    }

                </td>


                <td>

                    <span class="${resultClass}">

                        ${escapeHtml(
                            formatFailureReason(
                                log.result
                            )
                        )}

                    </span>

                </td>


                <td>

                    ${formatCurrency(
                        log.recovered_amount
                    )}

                </td>


                <td>

                    ${escapeHtml(
                        log.message
                    )}

                </td>

            `;


            table.appendChild(
                row
            );

        });

    }
    catch (error) {

        console.error(error);

        showNotification(
            "Unable to load audit trail"
        );

    }

}


/* =====================================================
   AUDIT TIME
===================================================== */

function formatAuditTime(
    timestamp
) {

    if (!timestamp) {

        return "-";

    }


    const date =
        new Date(timestamp);


    return date.toLocaleString(
        "en-IN"
    );

}


/* =====================================================
   FAQ
===================================================== */

function toggleFaq(button) {

    const card =
        button.closest(
            ".faq-card"
        );


    if (!card) {
        return;
    }


    document
        .querySelectorAll(
            ".faq-card"
        )
        .forEach(item => {

            if (
                item !== card
            ) {

                item.classList.remove(
                    "open"
                );

            }

        });


    card.classList.toggle(
        "open"
    );

}


/* =====================================================
   TEST PAYMENT
===================================================== */

function runTestPayment() {

    const customer =
        document.getElementById(
            "testCustomer"
        )?.value ||
        "Customer";


    const amount =
        document.getElementById(
            "testAmount"
        )?.value ||
        0;


    const status =
        document.getElementById(
            "testStatus"
        )?.value ||
        "failed";


    const reason =
        document.getElementById(
            "testReason"
        )?.value ||
        "unknown";


    if (
        status ===
        "success"
    ) {

        showNotification(
            `Test payment for ${customer} marked successful.`
        );

        return;

    }


    showNotification(
        `Test payment failed: ${
            formatFailureReason(reason)
        } — ₹${
            Number(amount)
                .toLocaleString("en-IN")
        }`
    );


    const matchingTransaction =
        allRiskTransactions.find(
            transaction =>
                transaction.failure_reason ===
                reason
        );


    if (
        matchingTransaction
    ) {

        setTimeout(() => {

            diagnose(
                matchingTransaction.transaction_id
            );

        }, 700);

    }

}


/* =====================================================
   REFRESH / GENERATE
===================================================== */

function generateTestTransactions() {

    showNotification(
        "Refreshing latest transaction set..."
    );


    loadDashboard();

}


/* =====================================================
   LOAD EVERYTHING
===================================================== */

async function loadDashboard() {

    await loadSummary();

    await loadRiskTransactions();

    await loadAuditLog();

}


/* =====================================================
   INITIALIZE
===================================================== */

window.addEventListener(
    "DOMContentLoaded",
    () => {

        setupNavigation();


        const hash =
            window.location.hash
                .replace(
                    "#",
                    ""
                );


        const section =
            hash ||
            "dashboard-section";


        const validSection =
            document.getElementById(
                section
            )
                ? section
                : "dashboard-section";


        showSection(
            validSection
        );

    }
);
