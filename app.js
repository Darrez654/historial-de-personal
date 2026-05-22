document.addEventListener('DOMContentLoaded', () => {
    // ==========================================================================
    // SELECCIÓN DE ELEMENTOS DEL DOM
    // ==========================================================================
    const appContainer = document.getElementById('app-container');
    const form = document.getElementById('dhp-form');
    const steps = Array.from(document.querySelectorAll('.form-step'));
    const stepItems = Array.from(document.querySelectorAll('.step-item'));
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const btnPrint = document.getElementById('btn-print');
    
    // Utilidades y configuraciones
    const btnExport = document.getElementById('btn-export');
    const btnImportTrigger = document.getElementById('btn-import-trigger');
    const importFile = document.getElementById('import-file');
    const btnClear = document.getElementById('btn-clear');
    const themeToggle = document.getElementById('theme-toggle');
    const saveStatusText = document.getElementById('save-status-text');
    const inputPhoto = document.getElementById('input-photo');
    const avatarImg = document.getElementById('avatar-img');
    const avatarPreviewBox = document.getElementById('avatar-preview-box');
    const printAvatarImg = document.getElementById('print-avatar-img');
    const printPhotoBox = document.getElementById('print-photo-box');
    
    let currentStep = 1;
    let photoBase64 = "";

    // ==========================================================================
    // CONFIGURACIÓN DE FILAS PREDEFINIDAS E INTERFACES REPETITIVAS
    // ==========================================================================
    
    // Límites y contenedores para datos tabulares (según formato de planilla oficial)
    const tablesConfig = {
        familiares: {
            containerId: 'familiares-container',
            printTableId: 'print-fam-table',
            rowsCount: 5,
            fields: ['primer_apellido', 'segundo_apellido', 'primer_nombre', 'segundo_nombre', 'civ'],
            placeholders: ['1er Apellido', '2do Apellido', '1er Nombre', '2do Nombre', 'Cédula de Identidad']
        },
        familiaresExterior: {
            containerId: 'familiares-exterior-container',
            printTableId: 'print-fam-ext-table',
            rowsCount: 3,
            fields: ['nombre_apellido', 'ci', 'parentesco', 'edad', 'direccion'],
            placeholders: ['Nombre y Apellido', 'Cédula N°', 'Parentesco', 'Edad', 'Dirección de Habitación']
        },
        viajes: {
            containerId: 'viajes-container',
            printTableId: 'print-viajes-table',
            rowsCount: 3,
            fields: ['desde', 'hasta', 'pais', 'motivo', 'direccion'],
            placeholders: ['Desde (MM/AAAA)', 'Hasta (MM/AAAA)', 'País Visitado', 'Motivo del Viaje', 'Dirección de Estadía']
        },
        laboral: {
            containerId: 'laboral-container',
            printTableId: 'print-laboral-table',
            rowsCount: 4,
            fields: ['desde', 'hasta', 'cargo', 'empresa', 'motivo'],
            placeholders: ['Desde (MM/AAAA)', 'Hasta (MM/AAAA)', 'Cargo Desempeñado', 'Nombre y Dirección de Empresa', 'Motivo del Retiro']
        },
        social: {
            containerId: 'social-container',
            printTableId: 'print-social-table',
            rowsCount: 3,
            fields: ['organizacion', 'direccion', 'actividades'],
            placeholders: ['Nombre de la Organización', 'Dirección', 'Actividades de la Organización']
        }
    };

    // Datos educativos (Etapas fijas en la planilla DHP oficial)
    const eduStages = [
        { key: 'primaria', label: 'Primaria' },
        { key: 'secundaria', label: 'Secundaria' },
        { key: 'diversificada', label: 'Diversificada' },
        { key: 'universitaria', label: 'Universitaria' },
        { key: 'maestria', label: 'Maestría' },
        { key: 'doctorado', label: 'Doctorado' },
        { key: 'otros', label: 'Otros (especialización)' }
    ];

    // ==========================================================================
    // INICIALIZACIÓN DE LA UI DINÁMICA
    // ==========================================================================

    // 1. Generar campos de educación en el formulario e impresión
    const eduInputsContainer = document.getElementById('edu-inputs-container');
    const printEduBody = document.querySelector('#print-educativo-table tbody');
    
    eduInputsContainer.innerHTML = '';
    printEduBody.innerHTML = '';
    
    // Fila cabecera educativa para pantallas grandes
    const headerRow = document.createElement('div');
    headerRow.className = 'edu-grid-row edu-grid-header';
    headerRow.innerHTML = `
        <div>Etapa</div>
        <div>Fecha Desde</div>
        <div>Fecha Hasta</div>
        <div>Nombre del Instituto</div>
        <div>Dirección</div>
        <div>Observaciones</div>
    `;
    eduInputsContainer.appendChild(headerRow);

    eduStages.forEach(stage => {
        // Fila en el formulario de pantalla
        const formRow = document.createElement('div');
        formRow.className = 'edu-grid-row';
        formRow.innerHTML = `
            <div class="edu-label">${stage.label}</div>
            <div class="form-group"><input type="text" id="f_edu_desde_${stage.key}" placeholder="MM/AAAA"></div>
            <div class="form-group"><input type="text" id="f_edu_hasta_${stage.key}" placeholder="MM/AAAA"></div>
            <div class="form-group"><input type="text" id="f_edu_inst_${stage.key}" placeholder="Nombre de la Institución"></div>
            <div class="form-group"><input type="text" id="f_edu_dir_${stage.key}" placeholder="Dirección"></div>
            <div class="form-group"><input type="text" id="f_edu_obs_${stage.key}" placeholder="Observaciones"></div>
        `;
        eduInputsContainer.appendChild(formRow);

        // Fila en la planilla oficial de impresión
        const printRow = document.createElement('tr');
        printRow.className = 'row-h-md';
        printRow.innerHTML = `
            <td class="text-bold font-xxs bg-gray">${stage.label.toUpperCase()}</td>
            <td id="p_edu_desde_${stage.key}" class="font-xs"></td>
            <td id="p_edu_hasta_${stage.key}" class="font-xs"></td>
            <td id="p_edu_inst_${stage.key}" class="font-xs text-left cell-padding-l"></td>
            <td id="p_edu_dir_${stage.key}" class="font-xs text-left cell-padding-l"></td>
            <td id="p_edu_obs_${stage.key}" class="font-xs text-left cell-padding-l"></td>
        `;
        printEduBody.appendChild(printRow);
    });

    // 2. Inicializar tablas de familiares, exterior, laboral, etc. en pantalla e impresión
    Object.keys(tablesConfig).forEach(key => {
        const config = tablesConfig[key];
        const container = document.getElementById(config.containerId);
        const printTableBody = document.querySelector(`#${config.printTableId} tbody`);
        
        container.innerHTML = '';
        printTableBody.innerHTML = '';
        
        // Crear las filas estáticas de impresión vacías para asegurar estructura exacta
        for (let i = 0; i < config.rowsCount; i++) {
            const printTr = document.createElement('tr');
            printTr.className = 'row-h-md';
            
            let cellsHTML = '';
            if (key === 'viajes' || key === 'laboral') {
                // Estas dos tablas tienen dos columnas de fecha separadas que colapsan en el encabezado
                cellsHTML = `
                    <td id="p_${key}_desde_${i}" class="col-10"></td>
                    <td id="p_${key}_hasta_${i}" class="col-10"></td>
                `;
                config.fields.slice(2).forEach((f, fieldIdx) => {
                    const colClass = fieldIdx === 0 ? 'col-25' : (fieldIdx === 1 ? 'col-30' : 'col-25');
                    cellsHTML += `<td id="p_${key}_${f}_${i}" class="${colClass} text-left cell-padding-l"></td>`;
                });
            } else {
                config.fields.forEach((f, fieldIdx) => {
                    const colClass = key === 'familiares' ? 'col-20' : 
                                     (key === 'familiaresExterior' ? (fieldIdx === 0 ? 'col-30' : fieldIdx === 3 ? 'col-10' : fieldIdx === 4 ? 'col-30' : 'col-15') :
                                     (fieldIdx === 2 ? 'col-40' : 'col-30'));
                    
                    const alignClass = (key === 'familiaresExterior' && (fieldIdx === 0 || fieldIdx === 4)) || 
                                       (key === 'social' && fieldIdx !== 2) ? 'text-left cell-padding-l' : '';
                    
                    cellsHTML += `<td id="p_${key}_${f}_${i}" class="${colClass} ${alignClass}"></td>`;
                });
            }
            printTr.innerHTML = cellsHTML;
            printTableBody.appendChild(printTr);
        }

        // Agregar la primera fila vacía al formulario en pantalla por defecto
        addRowToScreen(key);
    });

    // Función para agregar filas dinámicas en el formulario
    function addRowToScreen(tableKey, dataValues = null) {
        const config = tablesConfig[tableKey];
        const container = document.getElementById(config.containerId);
        const currentRowsCount = container.children.length;
        
        if (currentRowsCount >= config.rowsCount) {
            alert(`Para mantener el formato estricto de la planilla de 4 páginas, solo se permiten un máximo de ${config.rowsCount} registros en esta sección.`);
            return;
        }

        const rowDiv = document.createElement('div');
        rowDiv.className = 'repeating-row';
        rowDiv.dataset.index = currentRowsCount;

        // Botón de remoción (solo si no es el primer campo obligatorio de la referencia u otros)
        let removeBtnHTML = '';
        if (currentRowsCount > 0) {
            removeBtnHTML = `
                <button type="button" class="btn-remove-row" onclick="removeDynamicRow('${tableKey}', ${currentRowsCount})">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    Eliminar
                </button>
            `;
        }

        let inputsHTML = `<div class="grid-form">`;
        config.fields.forEach((field, idx) => {
            const val = dataValues ? (dataValues[field] || '') : '';
            const type = (field === 'desde' || field === 'hasta') && (tableKey !== 'viajes' && tableKey !== 'laboral') ? 'date' : 'text';
            const placeholder = config.placeholders[idx];
            
            inputsHTML += `
                <div class="form-group">
                    <label>${placeholder}</label>
                    <input type="${type}" id="f_${tableKey}_${field}_${currentRowsCount}" value="${val}" placeholder="${placeholder}">
                </div>
            `;
        });
        inputsHTML += `</div>${removeBtnHTML}`;

        rowDiv.innerHTML = inputsHTML;
        container.appendChild(rowDiv);

        // Asociar eventos inmediatos de sincronización
        config.fields.forEach(field => {
            const inputEl = document.getElementById(`f_${tableKey}_${field}_${currentRowsCount}`);
            if (inputEl) {
                inputEl.addEventListener('input', () => syncDynamicTable(tableKey));
            }
        });
    }

    // Hacer la remoción disponible globalmente para el controlador onclick inline
    window.removeDynamicRow = (tableKey, index) => {
        const config = tablesConfig[tableKey];
        const container = document.getElementById(config.containerId);
        
        if (container.children.length <= 1) return;

        // Eliminar del DOM en pantalla
        container.removeChild(container.children[index]);
        
        // Re-indexar los elementos restantes en pantalla
        Array.from(container.children).forEach((row, newIdx) => {
            row.dataset.index = newIdx;
            
            // Re-indexar inputs y labels
            const inputs = row.querySelectorAll('input');
            config.fields.forEach((field, fIdx) => {
                const input = inputs[fIdx];
                if (input) {
                    input.id = `f_${tableKey}_${field}_${newIdx}`;
                }
            });

            // Re-indexar botón eliminar
            const btnRemove = row.querySelector('.btn-remove-row');
            if (btnRemove) {
                btnRemove.setAttribute('onclick', `removeDynamicRow('${tableKey}', ${newIdx})`);
            }
        });

        // Limpiar completamente las filas de impresión correspondientes y re-sincronizar
        for (let i = 0; i < config.rowsCount; i++) {
            config.fields.forEach(field => {
                const printCell = document.getElementById(`p_${tableKey}_${field}_${i}`);
                if (printCell) printCell.textContent = '';
            });
        }

        // Ejecutar re-sincronización con los datos recolocados
        syncDynamicTable(tableKey);
        triggerAutoSave();
    };

    // Botones para agregar filas
    document.getElementById('btn-add-familiar').addEventListener('click', () => addRowToScreen('familiares'));
    document.getElementById('btn-add-familiar-ext').addEventListener('click', () => addRowToScreen('familiaresExterior'));
    document.getElementById('btn-add-viaje').addEventListener('click', () => addRowToScreen('viajes'));
    document.getElementById('btn-add-laboral').addEventListener('click', () => addRowToScreen('laboral'));
    document.getElementById('btn-add-social').addEventListener('click', () => addRowToScreen('social'));


    // ==========================================================================
    // SISTEMA DE SINCRONIZACIÓN BIDIRECCIONAL (FORM -> PRINT LAYOUT)
    // ==========================================================================

    // Sincronizar campos de entrada simples
    function syncSimpleFields() {
        // Mapeo directo: ID de pantalla -> ID de impresión
        const directMapping = {
            'f_primer_apellido': 'p_primer_apellido',
            'f_segundo_apellido': 'p_segundo_apellido',
            'f_primer_nombre': 'p_primer_nombre',
            'f_segundo_nombre': 'p_segundo_nombre',
            'f_lugar_nac': 'p_lugar_nac',
            'f_municipio': 'p_municipio',
            'f_estado': 'p_estado',
            'f_pais': 'p_pais',
            'f_cedula': 'p_cedula',
            'f_direccion': 'p_direccion',
            'f_telefono_hab': 'p_telefono_hab',
            'f_celular': 'p_celular',
            'f_otro_tlf': 'p_otro_tlf',
            'f_correo': 'p_correo',
            'f_profesion': 'p_profesion',
            'f_religion': 'p_religion',
            'f_edo_civil': 'p_edo_civil',
            'f_facebook': 'p_facebook',
            'f_twitter': 'p_twitter',
            'f_instagram': 'p_instagram',
            'f_badoo': 'p_badoo',
            'f_otras_redes': 'p_otras_redes',
            'f_cargo_nom': 'p_cargo_nom',
            'f_cargo_ocupa': 'p_cargo_ocupa',
            
            // Fisonómicas
            'f_contextura': 'p_contextura',
            'f_color_piel': 'p_color_piel',
            'f_cara': 'p_cara',
            'f_cabello': 'p_cabello',
            'f_frente': 'p_frente',
            'f_cejas': 'p_cejas',
            'f_ojos': 'p_ojos',
            'f_nariz': 'p_nariz',
            'f_labios': 'p_labios',
            'f_barba': 'p_barba',
            'f_estatura': 'p_estatura',
            'f_senales_partic': 'p_senales_partic',

            // Militares
            'f_mil_arma': 'p_mil_arma',
            'f_mil_promo': 'p_mil_promo',
            'f_mil_serial': 'p_mil_serial',
            'f_mil_unidad': 'p_mil_unidad',
            'f_mil_comandante': 'p_mil_comandante',

            // Referencias
            'f_ref_nom_1': 'p_ref_nom_1', 'f_ref_ci_1': 'p_ref_ci_1', 'f_ref_dir_1': 'p_ref_dir_1',
            'f_ref_nom_2': 'p_ref_nom_2', 'f_ref_ci_2': 'p_ref_ci_2', 'f_ref_dir_2': 'p_ref_dir_2',
            'f_ref_nom_3': 'p_ref_nom_3', 'f_ref_ci_3': 'p_ref_ci_3', 'f_ref_dir_3': 'p_ref_dir_3',

            // Administrativos
            'f_adm_cant_cuentas': 'p_adm_cant_cuentas',
            'f_adm_desc_cuentas': 'p_adm_desc_cuentas',
            
            'f_veh_marca': 'p_veh_marca',
            'f_veh_ano': 'p_veh_ano',
            'f_veh_modelo': 'p_veh_modelo',
            'f_veh_placa': 'p_veh_placa',
            'f_veh_tipo': 'p_veh_tipo',
            'f_veh_color': 'p_veh_color',

            'f_arma_marca': 'p_arma_marca',
            'f_arma_modelo': 'p_arma_modelo',
            'f_arma_serial': 'p_arma_serial',
            'f_arma_permiso': 'p_arma_permiso',

            'f_det_causa': 'p_det_causa',
            'f_det_lugar': 'p_det_lugar',
            'f_part_especifique': 'p_part_especifique',
            'f_part_lugar': 'p_part_lugar',
            'f_seg_incidente': 'p_seg_incidente',
            
            'f_fre_sitios': 'p_fre_sitios',
            'f_fre_hobby': 'p_fre_hobby',
            'f_fre_deporte': 'p_fre_deporte'
        };

        // Transferir texto plano
        Object.keys(directMapping).forEach(srcId => {
            const srcEl = document.getElementById(srcId);
            const dstEl = document.getElementById(directMapping[srcId]);
            if (srcEl && dstEl) {
                dstEl.textContent = srcEl.value || '';
            }
        });

        // Formatear fechas para impresión (DD/MM/AAAA)
        const dateMapping = {
            'f_fecha_nac': 'p_fecha_nac',
            'f_mil_fecha_grado': 'p_mil_fecha_grado'
        };

        Object.keys(dateMapping).forEach(srcId => {
            const srcEl = document.getElementById(srcId);
            const dstEl = document.getElementById(dateMapping[srcId]);
            if (srcEl && dstEl) {
                dstEl.textContent = formatDateString(srcEl.value);
            }
        });

        // Control num planilla en cabecera
        const numControlEl = document.getElementById('f_num_control');
        const printNumControlEl = document.getElementById('print_num_control');
        if (numControlEl && printNumControlEl) {
            printNumControlEl.textContent = numControlEl.value ? numControlEl.value : '___________';
        }

        // Cuerpo Policial y Fecha (combinado en formato oficial)
        const detCuerpoEl = document.getElementById('f_det_cuerpo');
        const detFechaEl = document.getElementById('f_det_fecha');
        const pDetCuerpoFechaEl = document.getElementById('p_det_cuerpo_fecha');
        if (detCuerpoEl && detFechaEl && pDetCuerpoFechaEl) {
            const cuerpo = detCuerpoEl.value || 'N/A';
            const fecha = detFechaEl.value || 'N/A';
            pDetCuerpoFechaEl.textContent = `${cuerpo} / FECHA: ${fecha}`;
        }

        // Sincronizar Casillas Checkbox (SI / NO)
        syncCheckboxes('f_whatsapp', 'p_whatsapp_si', 'p_whatsapp_no');
        syncCheckboxes('f_mil_cumplio_servicio', 'p_mil_servicio_si', 'p_mil_servicio_no');
        syncCheckboxes('f_adm_posee_cuentas', 'p_adm_cuentas_si', 'p_adm_cuentas_no');
        syncCheckboxes('f_adm_posee_vehiculo', 'p_veh_si', 'p_veh_no');
        syncCheckboxes('f_adm_posee_arma', 'p_arma_si', 'p_arma_no');
        syncCheckboxes('f_seg_detenido', 'p_detenido_si', 'p_detenido_no');
        syncCheckboxes('f_seg_partido', 'p_partido_si', 'p_partido_no');

        // Sincronizar bloque educativo
        eduStages.forEach(stage => {
            ['desde', 'hasta', 'inst', 'dir', 'obs'].forEach(f => {
                const src = document.getElementById(`f_edu_${f}_${stage.key}`);
                const dst = document.getElementById(`p_edu_${f}_${stage.key}`);
                if (src && dst) {
                    dst.textContent = src.value || '';
                }
            });
        });
    }

    // Auxiliar para checkboxes con 'X'
    function syncCheckboxes(srcSelectId, dstSiId, dstNoId) {
        const srcEl = document.getElementById(srcSelectId);
        const dstSi = document.getElementById(dstSiId);
        const dstNo = document.getElementById(dstNoId);
        
        if (srcEl && dstSi && dstNo) {
            const val = srcEl.value;
            if (val === 'SI') {
                dstSi.textContent = 'X';
                dstNo.textContent = '';
            } else if (val === 'NO') {
                dstSi.textContent = '';
                dstNo.textContent = 'X';
            } else {
                dstSi.textContent = '';
                dstNo.textContent = '';
            }
        }
    }

    // Formateador de fecha
    function formatDateString(val) {
        if (!val) return '';
        const parts = val.split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return val;
    }

    // Sincronizar Tablas Dinámicas
    function syncDynamicTable(tableKey) {
        const config = tablesConfig[tableKey];
        const container = document.getElementById(config.containerId);
        const activeRows = container.children.length;

        for (let i = 0; i < config.rowsCount; i++) {
            config.fields.forEach(field => {
                const printCell = document.getElementById(`p_${tableKey}_${field}_${i}`);
                if (printCell) {
                    if (i < activeRows) {
                        const inputEl = document.getElementById(`f_${tableKey}_${field}_${i}`);
                        printCell.textContent = inputEl ? inputEl.value : '';
                    } else {
                        printCell.textContent = ''; // Limpio si no hay datos cargados
                    }
                }
            });
        }
    }

    // Vincular listeners generales en todos los campos base del formulario
    form.addEventListener('input', () => {
        syncSimpleFields();
        triggerAutoSave();
    });
    form.addEventListener('change', () => {
        syncSimpleFields();
        triggerAutoSave();
    });


    // ==========================================================================
    // SISTEMA DE ASISTENTE PASO A PASO (WIZARD NAV)
    // ==========================================================================

    function showStep(stepNum) {
        steps.forEach(step => step.classList.remove('active'));
        stepItems.forEach(item => item.classList.remove('active'));

        const targetStep = steps.find(s => parseInt(s.dataset.step) === stepNum);
        const targetItem = stepItems.find(i => parseInt(i.dataset.step) === stepNum);

        if (targetStep) targetStep.classList.add('active');
        if (targetItem) targetItem.classList.add('active');

        // Controlar visibilidad de botones
        btnPrev.style.display = stepNum === 1 ? 'none' : 'flex';
        
        if (stepNum === steps.length) {
            btnNext.style.display = 'none';
            btnPrint.style.display = 'flex';
        } else {
            btnNext.style.display = 'flex';
            btnPrint.style.display = 'none';
        }

        currentStep = stepNum;
        
        // Hacer scroll suave al inicio del panel
        document.querySelector('.main-content').scrollTop = 0;
    }

    // Navegar al hacer click en la barra lateral
    stepItems.forEach(item => {
        item.addEventListener('click', () => {
            const stepNum = parseInt(item.dataset.step);
            // Permitir navegación libre si el formulario ya ha sido validado o simplemente para facilitar
            showStep(stepNum);
        });
    });

    btnPrev.addEventListener('click', () => {
        if (currentStep > 1) {
            showStep(currentStep - 1);
        }
    });

    btnNext.addEventListener('click', () => {
        if (validateCurrentStep()) {
            // Marcar paso actual como completado en la UI
            const currentItem = stepItems.find(i => parseInt(i.dataset.step) === currentStep);
            if (currentItem) currentItem.classList.add('completed');
            
            showStep(currentStep + 1);
        }
    });

    // Validar campos requeridos en el paso actual (Desactivado para navegación libre y revisión flexible)
    function validateCurrentStep() {
        return true;
    }


    // ==========================================================================
    // PROCESAMIENTO DE FOTOGRAFÍA CARNET
    // ==========================================================================

    inputPhoto.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 2 * 1024 * 1024) {
            alert("La fotografía es muy pesada. Cargue una imagen de máximo 2 MB.");
            return;
        }

        const reader = new FileReader();
        reader.onload = function(evt) {
            photoBase64 = evt.target.result;
            
            // Renderizar en UI interactiva
            avatarImg.src = photoBase64;
            avatarImg.style.display = 'block';
            avatarPreviewBox.querySelector('.avatar-placeholder').style.display = 'none';

            // Renderizar en Planilla de Impresión Oficial
            printAvatarImg.src = photoBase64;
            printAvatarImg.style.display = 'block';
            printPhotoBox.querySelector('.photo-txt').style.display = 'none';

            triggerAutoSave();
        };
        reader.readAsDataURL(file);
    });


    // ==========================================================================
    // AUTO-GUARDADO LOCAL (LOCALSTORAGE) Y BACKUP
    // ==========================================================================

    let autoSaveTimeout = null;

    function triggerAutoSave() {
        saveStatusText.textContent = "Escribiendo borrador...";
        document.querySelector('.indicator-dot').classList.remove('status-saved');

        if (autoSaveTimeout) clearTimeout(autoSaveTimeout);
        
        autoSaveTimeout = setTimeout(() => {
            saveDataToLocalStorage();
        }, 1000); // Guarda tras 1 segundo de inactividad de escritura
    }

    function saveDataToLocalStorage() {
        const formData = compileFormState();
        localStorage.setItem('dhp_draft_data', JSON.stringify(formData));
        
        saveStatusText.textContent = "Borrador guardado localmente";
        document.querySelector('.indicator-dot').classList.add('status-saved');
    }

    function compileFormState() {
        const state = {
            photo: photoBase64,
            theme: document.body.classList.contains('dark-theme') ? 'dark' : 'light',
            simpleFields: {},
            dynamicTables: {},
            education: {}
        };

        // 1. Campos Simples
        const simpleInputIds = [
            'f_primer_apellido', 'f_segundo_apellido', 'f_primer_nombre', 'f_segundo_nombre',
            'f_fecha_nac', 'f_lugar_nac', 'f_cedula', 'f_edo_civil', 'f_pais', 'f_estado', 'f_municipio',
            'f_profesion', 'f_religion', 'f_num_control', 'f_direccion', 'f_telefono_hab', 'f_celular',
            'f_otro_tlf', 'f_correo', 'f_facebook', 'f_whatsapp', 'f_twitter', 'f_instagram', 'f_badoo',
            'f_otras_redes', 'f_cargo_nom', 'f_cargo_ocupa', 'f_contextura', 'f_color_piel', 'f_cara',
            'f_cabello', 'f_frente', 'f_cejas', 'f_ojos', 'f_nariz', 'f_labios', 'f_barba', 'f_estatura',
            'f_senales_partic', 'f_mil_arma', 'f_mil_fecha_grado', 'f_mil_promo', 'f_mil_serial',
            'f_mil_cumplio_servicio', 'f_mil_unidad', 'f_mil_comandante', 
            'f_ref_nom_1', 'f_ref_ci_1', 'f_ref_dir_1',
            'f_ref_nom_2', 'f_ref_ci_2', 'f_ref_dir_2',
            'f_ref_nom_3', 'f_ref_ci_3', 'f_ref_dir_3',
            'f_adm_posee_cuentas', 'f_adm_cant_cuentas', 'f_adm_desc_cuentas',
            'f_adm_posee_vehiculo', 'f_veh_marca', 'f_veh_ano', 'f_veh_modelo', 'f_veh_placa', 'f_veh_tipo', 'f_veh_color',
            'f_adm_posee_arma', 'f_arma_marca', 'f_arma_modelo', 'f_arma_serial', 'f_arma_permiso',
            'f_seg_detenido', 'f_det_causa', 'f_det_cuerpo', 'f_det_fecha', 'f_det_lugar',
            'f_seg_partido', 'f_part_especifique', 'f_part_lugar', 'f_seg_incidente',
            'f_fre_sitios', 'f_fre_hobby', 'f_fre_deporte'
        ];

        simpleInputIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) state.simpleFields[id] = el.value;
        });

        // 2. Tablas Dinámicas
        Object.keys(tablesConfig).forEach(key => {
            const config = tablesConfig[key];
            const container = document.getElementById(config.containerId);
            const rowCount = container.children.length;
            
            state.dynamicTables[key] = [];
            
            for (let i = 0; i < rowCount; i++) {
                const rowData = {};
                config.fields.forEach(field => {
                    const inputEl = document.getElementById(`f_${key}_${field}_${i}`);
                    if (inputEl) {
                        rowData[field] = inputEl.value;
                    }
                });
                state.dynamicTables[key].push(rowData);
            }
        });

        // 3. Educación
        eduStages.forEach(stage => {
            state.education[stage.key] = {};
            ['desde', 'hasta', 'inst', 'dir', 'obs'].forEach(f => {
                const el = document.getElementById(`f_edu_${f}_${stage.key}`);
                if (el) state.education[stage.key][f] = el.value;
            });
        });

        return state;
    }

    function loadFormState(state) {
        if (!state) return;

        // 1. Cargar Foto
        if (state.photo) {
            photoBase64 = state.photo;
            avatarImg.src = photoBase64;
            avatarImg.style.display = 'block';
            avatarPreviewBox.querySelector('.avatar-placeholder').style.display = 'none';

            printAvatarImg.src = photoBase64;
            printAvatarImg.style.display = 'block';
            printPhotoBox.querySelector('.photo-txt').style.display = 'none';
        } else {
            photoBase64 = "";
            avatarImg.src = "";
            avatarImg.style.display = 'none';
            avatarPreviewBox.querySelector('.avatar-placeholder').style.display = 'block';

            printAvatarImg.src = "";
            printAvatarImg.style.display = 'none';
            printPhotoBox.querySelector('.photo-txt').style.display = 'block';
        }

        // 2. Cargar Tema
        if (state.theme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.querySelector('.sun-icon').style.display = 'none';
            themeToggle.querySelector('.moon-icon').style.display = 'block';
        } else {
            document.body.classList.remove('dark-theme');
            themeToggle.querySelector('.sun-icon').style.display = 'block';
            themeToggle.querySelector('.moon-icon').style.display = 'none';
        }

        // 3. Cargar Campos Simples
        if (state.simpleFields) {
            Object.keys(state.simpleFields).forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = state.simpleFields[id];
            });
        }

        // 4. Cargar Tablas Dinámicas
        if (state.dynamicTables) {
            Object.keys(tablesConfig).forEach(key => {
                const config = tablesConfig[key];
                const container = document.getElementById(config.containerId);
                
                // Vaciar container en UI de pantalla
                container.innerHTML = '';
                
                const rowsData = state.dynamicTables[key] || [];
                if (rowsData.length === 0) {
                    // Generar al menos una fila vacía por defecto
                    addRowToScreen(key);
                } else {
                    rowsData.forEach(rowData => {
                        addRowToScreen(key, rowData);
                    });
                }
                
                // Sincronizar con vista de impresión
                syncDynamicTable(key);
            });
        }

        // 5. Cargar Educación
        if (state.education) {
            eduStages.forEach(stage => {
                const eduData = state.education[stage.key] || {};
                ['desde', 'hasta', 'inst', 'dir', 'obs'].forEach(f => {
                    const el = document.getElementById(`f_edu_${f}_${stage.key}`);
                    if (el) el.value = eduData[f] || '';
                });
            });
        }

        // Sincronizar todos los textos en planilla final de impresión
        syncSimpleFields();
        
        saveStatusText.textContent = "Borrador cargado";
        document.querySelector('.indicator-dot').classList.add('status-saved');
    }

    // Intentar leer de LocalStorage al iniciar
    function tryLoadFromLocalStorage() {
        try {
            const raw = localStorage.getItem('dhp_draft_data');
            if (raw) {
                const parsed = JSON.parse(raw);
                loadFormState(parsed);
            }
        } catch (e) {
            console.error("Error cargando borrador local:", e);
        }
    }


    // ==========================================================================
    // EXPORTAR E IMPORTAR COPIAS DE SEGURIDAD (RESPALDO JSON)
    // ==========================================================================

    btnExport.addEventListener('click', () => {
        const state = compileFormState();
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state, null, 2));
        const downloadAnchor = document.createElement('a');
        
        const cedula = document.getElementById('f_cedula').value.trim() || 'SIN_CEDULA';
        const apellido = document.getElementById('f_primer_apellido').value.trim() || 'DECLARANTE';
        
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `DHP_Respaldo_${cedula}_${apellido.toUpperCase()}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    });

    btnImportTrigger.addEventListener('click', () => {
        importFile.click();
    });

    importFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function(evt) {
            try {
                const parsed = JSON.parse(evt.target.result);
                loadFormState(parsed);
                saveDataToLocalStorage();
                alert("Respaldo de datos importado y cargado con éxito.");
            } catch (err) {
                alert("Error: El archivo seleccionado no es un archivo de respaldo de planilla DHP válido.");
            }
        };
        reader.readAsText(file);
        // Reset del input para permitir cargar el mismo archivo consecutivamente si es necesario
        importFile.value = '';
    });


    // ==========================================================================
    // LIMPIEZA DE FORMULARIO
    // ==========================================================================

    btnClear.addEventListener('click', () => {
        if (confirm("¿Está completamente seguro de que desea limpiar el formulario? Esto borrará permanentemente todos los datos ingresados y el borrador guardado en este navegador.")) {
            localStorage.removeItem('dhp_draft_data');
            
            // Recargar página limpia
            window.location.reload();
        }
    });


    // ==========================================================================
    // CONTROL DEL TEMA (OSCURO/CLARO)
    // ==========================================================================

    themeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-theme');
        
        themeToggle.querySelector('.sun-icon').style.display = isDark ? 'none' : 'block';
        themeToggle.querySelector('.moon-icon').style.display = isDark ? 'block' : 'none';

        triggerAutoSave();
    });


    // ==========================================================================
    // EJECUCIÓN E INICIALIZACIÓN
    // ==========================================================================

    tryLoadFromLocalStorage();

    // Evento de impresión
    btnPrint.addEventListener('click', () => {
        if (validateCurrentStep()) {
            window.print();
        }
    });
});
