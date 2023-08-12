function formatCzechDate(date) {
    return `${date.getDate()}. ${date.getMonth() + 1}. ${date.getFullYear()}`
}

function parseCzechDate(dateStr) {
    const [day, month, year] = dateStr.split('.')
    return new Date(year, month - 1, day, 0, 0, 0, 0)
}