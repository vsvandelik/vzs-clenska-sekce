document.addEventListener("DOMContentLoaded", hideUnnecessaryFields);
document.getElementById("display-hidden-fields").addEventListener("click", displayHiddenFields);

const unnecessaryFields = [
    "date_of_birth",
    "birth_number",
    "health_insurance_company",
    "street",
    "city",
    "postcode",
    "swimming_time"
]
function hideUnnecessaryFields(){
    unnecessaryFields.forEach(field => {
        document.getElementById(`div_id_${field}`).style.display = "none";
    });
}

function displayHiddenFields(e){
    unnecessaryFields.forEach(field => {
        document.getElementById(`div_id_${field}`).style.display = "block";
    });
    e.target.classList.remove("d-inline-block");
    e.target.style.display = "none";
}

