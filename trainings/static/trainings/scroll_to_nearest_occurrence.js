document.addEventListener('DOMContentLoaded', function () {
    const occurrencesList = document.getElementById('occurrences-list');
    const nearestOccurrence = document.getElementById('nearest-occurrence');

    let scrollTo = nearestOccurrence.offsetLeft - nearestOccurrence.clientWidth;

    occurrencesList.scrollTo({
        left: scrollTo,
        behavior: 'smooth'
    });
});