/**
 * viewer.js — 3D визуализация с Three.js (ортографическая камера)
 */

class IFCViewer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f4f8);

        const width = canvasElement.clientWidth;
        const height = canvasElement.clientHeight;
        const aspect = width / height;
        const frustumSize = 800;

        this.camera = new THREE.OrthographicCamera(
            -frustumSize * aspect,
            frustumSize * aspect,
            -frustumSize,
            frustumSize,
            -10000.0,
            10000
        );
        this.camera.position.set(0, 0, 1000);
        this.camera.up.set(0, 1, 0);
        this.camera.lookAt(0, 0, 0);

        this.renderer = new THREE.WebGLRenderer({
            canvas: canvasElement,
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;

        this.setupLighting();
        this.setupControls();

        this.meshes = [];
        this.selectedMesh = null;
        this.focusPoint = new THREE.Vector3(0, 0, 0);
        this.assemblyInfo = null;

        window.addEventListener('resize', () => this.onWindowResize());

        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        canvasElement.addEventListener('click', (e) => this.onCanvasClick(e));

        this.animate();
    }

    setupLighting() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(300, 400, 200);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);

        // Сетка с повышенной контрастностью
        const gridHelper = new THREE.GridHelper(2000, 20, 0x888888, 0xaaaaaa);
        this.scene.add(gridHelper);

        const axesHelper = new THREE.AxesHelper(200);
        this.scene.add(axesHelper);
    }

    setupControls() {
        this.controls = {
            isDragging: false,
            isRotating: false,
            lastX: 0,
            lastY: 0,
            panSpeed: 2.0,
            rotationSpeed: 0.005
        };

        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) {
                this.controls.isRotating = true;
            } else if (e.button === 1) {
                this.controls.isDragging = true;
            }
            this.controls.lastX = e.clientX;
            this.controls.lastY = e.clientY;
        });

        this.canvas.addEventListener('mousemove', (e) => {
            const deltaX = e.clientX - this.controls.lastX;
            const deltaY = e.clientY - this.controls.lastY;

            if (this.controls.isDragging) {
                this.pan(deltaX, deltaY);
            } else if (this.controls.isRotating) {
                this.rotate(deltaX, deltaY);
            }

            this.controls.lastX = e.clientX;
            this.controls.lastY = e.clientY;
        });

        this.canvas.addEventListener('mouseup', (e) => {
            if (e.button === 0) {
                this.controls.isRotating = false;
            } else if (e.button === 1) {
                this.controls.isDragging = false;
            }
        });

        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());

        this.canvas.addEventListener(
            'wheel',
            (e) => {
                e.preventDefault();
                this.zoom(e.deltaY > 0 ? 1.1 : 0.9);
            },
            { passive: false }
        );
    }

    pan(deltaX, deltaY) {
        const frustumWidth = this.camera.right - this.camera.left;
        const frustumHeight = this.camera.top - this.camera.bottom;
        const moveSpeedX = frustumWidth / this.canvas.clientWidth;
        const moveSpeedY = frustumHeight / this.canvas.clientHeight;

        // Обновляем матрицу камеры для получения актуальных осей
        this.camera.updateMatrixWorld();

        // Получаем векторы осей камеры из матрицы
        const panX = new THREE.Vector3();
        const panY = new THREE.Vector3();

        // Извлекаем оси из матрицы камеры
        panX.setFromMatrixColumn(this.camera.matrixWorld, 0);
        panY.setFromMatrixColumn(this.camera.matrixWorld, 1);

        // Перемещаем камеру и точку фокуса по осям камеры
        const offset = new THREE.Vector3()
            .addScaledVector(panX, -deltaX * moveSpeedX)
            .addScaledVector(panY, -deltaY * moveSpeedY);

        this.camera.position.add(offset);
        this.focusPoint.add(offset);
        this.camera.lookAt(this.focusPoint);
    }

    rotate(deltaX, deltaY) {
        const rotationSpeed = 0.005;

        // Вектор от focusPoint к камере
        const offset = new THREE.Vector3().subVectors(this.camera.position, this.focusPoint);
        const distance = offset.length();

        // Создаём кватернионы для вращения
        const quaternionX = new THREE.Quaternion().setFromAxisAngle(
            new THREE.Vector3(1, 0, 0),
            deltaY * rotationSpeed
        );
        const quaternionY = new THREE.Quaternion().setFromAxisAngle(
            new THREE.Vector3(0, 1, 0),
            -deltaX * rotationSpeed
        );

        // Применяем вращение к вектору offset
        offset.applyQuaternion(quaternionY);
        offset.applyQuaternion(quaternionX);

        // Ограничиваем вертикальный угол
        const minPolarAngle = 0.01;
        const maxPolarAngle = Math.PI - 0.01;
        const spherical = new THREE.Spherical().setFromVector3(offset);
        spherical.phi = Math.max(minPolarAngle, Math.min(maxPolarAngle, spherical.phi));
        offset.setFromSpherical(spherical);

        // Обновляем позицию камеры
        this.camera.position.copy(this.focusPoint).add(offset);
        this.camera.lookAt(this.focusPoint);
    }

    zoom(factor) {
        this.camera.left *= factor;
        this.camera.right *= factor;
        this.camera.top *= factor;
        this.camera.bottom *= factor;
        this.camera.updateProjectionMatrix();
    }

    /**
     * Обновление мешей с сохранением вида камеры
     * @param {object} meshData
     * @param {boolean} preserveView — сохранить текущую ориентацию камеры
     */
    updateMeshes(meshData, preserveView = true) {
        const savedCameraState = preserveView
            ? {
                  position: this.camera.position.clone(),
                  focusPoint: this.focusPoint.clone()
              }
            : null;

        // Очистка старых мешей
        this.meshes.forEach((item) => {
            this.scene.remove(item.mesh);
            if (item.mesh.geometry) item.mesh.geometry.dispose();
            if (item.mesh.material) item.mesh.material.dispose();
        });
        this.meshes = [];
        this.assemblyInfo = null;

        if (!meshData || !meshData.meshes) {
            if (savedCameraState) {
                this.restoreCameraState(savedCameraState);
            }
            return;
        }

        // Сохранение информации о сборке
        if (meshData.assembly_info) {
            this.assemblyInfo = meshData.assembly_info;
        }

        // Создание новых мешей
        meshData.meshes.forEach((data, index) => {
            if (!data.vertices || !data.indices) return;

            const geometry = new THREE.BufferGeometry();
            const transformedVertices = this.transformVerticesForThreeJS(data.vertices);

            geometry.setAttribute(
                'position',
                new THREE.BufferAttribute(new Float32Array(transformedVertices), 3)
            );
            geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(data.indices), 1));

            // Используем готовые нормали если есть, иначе вычисляем
            if (data.normals && data.normals.length > 0) {
                geometry.setAttribute(
                    'normal',
                    new THREE.BufferAttribute(new Float32Array(data.normals), 3)
                );
            } else {
                geometry.computeVertexNormals();
            }

            const material = new THREE.MeshPhongMaterial({
                color: data.color || 0x2563eb,
                side: THREE.DoubleSide,
                shininess: 30,
                flatShading: true
            });

            const mesh = new THREE.Mesh(geometry, material);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            this.scene.add(mesh);

            this.meshes.push({
                mesh,
                id: data.id || `mesh_${index}`,
                name: data.name || `Component ${index}`,
                metadata: data.metadata || {}
            });
        });

        if (savedCameraState && this.meshes.length > 0) {
            this.restoreCameraState(savedCameraState);
        }

        // Отправляем событие с данными о сборке для обновления панели свойств
        if (this.assemblyInfo) {
            window.dispatchEvent(
                new CustomEvent('meshSelected', {
                    detail: {
                        id: 'assembly',
                        name: this.assemblyInfo.name || 'Assembly',
                        isAssembly: true,
                        assemblyInfo: this.assemblyInfo
                    }
                })
            );
        }
    }

    /**
     * Восстановление состояния камеры
     */
    restoreCameraState(state) {
        this.camera.position.copy(state.position);
        this.focusPoint.copy(state.focusPoint);
        this.camera.lookAt(this.focusPoint);
    }

    /**
     * Обновление мешей с фокусировкой на объектах
     * @param {object} meshData
     */
    updateMeshesAndFocus(meshData) {
        this.focusPoint.set(0, 0, 0);
        this.updateMeshes(meshData, false);
        if (this.meshes.length > 0) {
            this.frameAll();
        }
    }

    /**
     * Инициализация камеры с фокусировкой
     * @param {object} meshData
     */
    initializeCameraFocus(meshData) {
        this.focusPoint.set(0, 0, 0);
        this.updateMeshes(meshData, false);
        if (this.meshes.length > 0) {
            this.frameAll();
        }
    }

    /**
     * Трансформация вершин из IFC (Z-up, метры) в Three.js (Y-up, миллиметры)
     * @param {number[]} vertices
     * @returns {number[]}
     */
    transformVerticesForThreeJS(vertices) {
        const transformed = [];
        for (let i = 0; i < vertices.length; i += 3) {
            // Конвертация метров в миллиметры + трансформация осей
            // IFC: Z - вертикаль, Three.js: Y - вертикаль
            // Инверсия Z для правильного вида сверху
            transformed.push(
                vertices[i] * 1000, // x (м → мм)
                -vertices[i + 2] * 1000, // -z -> y (инверсия для вида сверху)
                -vertices[i + 1] * 1000 // -y -> z (м → мм)
            );
        }
        return transformed;
    }

    /**
     * Обработка клика по сцене
     */
    async onCanvasClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.meshes.map((item) => item.mesh));

        if (intersects.length > 0) {
            // Клик на элементе
            const meshItem = this.meshes.find((item) => item.mesh === intersects[0].object);
            if (meshItem) {
                this.selectMesh(meshItem);
                const boundingBox = new THREE.Box3().setFromObject(meshItem.mesh);
                const center = new THREE.Vector3();
                boundingBox.getCenter(center);
                this.focusPoint.copy(center);

                // Получаем PropertySet элемента
                const globalId = meshItem.metadata?.GlobalId;
                if (globalId && window.ifcBridge) {
                    const props = await window.ifcBridge.getElementProperties(globalId);
                    window.dispatchEvent(
                        new CustomEvent('meshSelected', {
                            detail: {
                                name: props?.name || meshItem.name,
                                ifc_type: props?.ifc_type || 'N/A',
                                elementProperties: props
                            }
                        })
                    );
                } else {
                    window.dispatchEvent(new CustomEvent('meshSelected', { detail: meshItem }));
                }
            }
        } else {
            // Клик на пустом месте — сборка
            this.deselectMesh();
            this.focusPoint.set(0, 0, 0);

            if (this.assemblyInfo?.globalId && window.ifcBridge) {
                const props = await window.ifcBridge.getElementProperties(
                    this.assemblyInfo.globalId
                );
                window.dispatchEvent(
                    new CustomEvent('meshSelected', {
                        detail: {
                            name: props?.name || this.assemblyInfo.name || 'Assembly',
                            ifc_type: props?.ifc_type || 'N/A',
                            elementProperties: props
                        }
                    })
                );
            }
        }
    }

    selectMesh(meshItem) {
        this.deselectMesh();
        this.selectedMesh = meshItem;
        meshItem.mesh.material.emissive.setHex(0xffff00);
        meshItem.mesh.material.emissiveIntensity = 0.3;

        const boundingBox = new THREE.Box3().setFromObject(meshItem.mesh);
        const center = new THREE.Vector3();
        boundingBox.getCenter(center);
        this.focusPoint.copy(center);
    }

    deselectMesh() {
        if (this.selectedMesh) {
            this.selectedMesh.mesh.material.emissive.setHex(0x000000);
            this.selectedMesh.mesh.material.emissiveIntensity = 0;
            this.selectedMesh = null;
            this.focusPoint.set(0, 0, 0);
        }
    }

    /**
     * Фокусировка камеры на всех объектах
     */
    frameAll() {
        if (this.meshes.length === 0) return;

        const box = new THREE.Box3();
        this.meshes.forEach((item) => box.expandByObject(item.mesh));

        const center = box.getCenter(new THREE.Vector3());

        const offset = new THREE.Vector3().subVectors(this.camera.position, this.focusPoint);
        const prevDistance = offset.length() || 1000;

        this.camera.position.set(center.x, center.y, center.z + prevDistance);
        this.camera.lookAt(center.x, center.y, center.z);
        this.focusPoint.copy(center);

        const size = box.getSize(new THREE.Vector3());
        const maxSize = Math.max(size.x, size.y) * 0.8;
        const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        const frustumSize = Math.max(maxSize, 200);

        this.camera.left = -frustumSize * aspect;
        this.camera.right = frustumSize * aspect;
        this.camera.top = frustumSize;
        this.camera.bottom = -frustumSize;
        this.camera.updateProjectionMatrix();

        this.applyCameraRotation();
    }

    /**
     * Применение текущего вращения камеры
     */
    applyCameraRotation() {
        const offset = new THREE.Vector3().subVectors(this.camera.position, this.focusPoint);
        const distance = offset.length();

        // Вычисляем текущие углы из позиции камеры
        const spherical = new THREE.Spherical().setFromVector3(offset);

        // Преобразуем в декартовы координаты
        const newOffset = new THREE.Vector3().setFromSpherical({
            radius: distance,
            phi: spherical.phi,
            theta: spherical.theta
        });

        this.camera.position.copy(this.focusPoint).add(newOffset);
        this.camera.lookAt(this.focusPoint);
    }

    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        const aspect = width / height;
        const frustumSize = (this.camera.right - this.camera.left) / 2;

        this.camera.left = -frustumSize * aspect;
        this.camera.right = frustumSize * aspect;
        this.camera.top = frustumSize;
        this.camera.bottom = -frustumSize;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.renderer.render(this.scene, this.camera);
    }
}

// ES6 export
export default IFCViewer;

// CommonJS export для обратной совместимости
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IFCViewer;
}
