/**
 * viewer.js - 3D визуализация с Three.js
 */

class IFCViewer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f4f8);

        const width = canvasElement.clientWidth;
        const height = canvasElement.clientHeight;

        // Определение параметров ортографической камеры
        const aspect = width / height;
        const frustumSize = 800; // Размер фрустума (половина высоты видимой области)
        
        this.camera = new THREE.OrthographicCamera(
            -frustumSize * aspect, // left
             frustumSize * aspect, // right
            -frustumSize,          // bottom
             frustumSize,          // top
             0.1,                 // near
             10000                // far
        );
        // Устанавливаем начальную позицию камеры для ориентации вдоль оси Z
        this.camera.position.set(0, 0, 1000);
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
        this.focusPoint = new THREE.Vector3(0, 0, 0); // Точка фокуса по умолчанию - начало координат
        this.firstRun = true; // Флаг для отслеживания первого запуска

        // Handle resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Click handling
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        canvasElement.addEventListener('click', (e) => this.onCanvasClick(e));

        // Start animation loop
        this.animate();
    }

    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        // Directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(300, 400, 200);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);

        // Grid helper
        const gridHelper = new THREE.GridHelper(2000, 20, 0xcccccc, 0xeeeeee);
        this.scene.add(gridHelper);

        // Axes helper (small)
        const axesHelper = new THREE.AxesHelper(200);
        this.scene.add(axesHelper);
    }

    setupControls() {
        // Controls for orthographic camera: pan, rotate, zoom
        this.controls = {
            isDragging: false,
            isRotating: false,
            lastX: 0,
            lastY: 0,
            panSpeed: 2.0,
            rotationSpeed: 0.005,
            currentRotationX: 0, // Начальное вращение X (вокруг горизонтальной оси)
            currentRotationY: 0, // Начальное вращение Y (вокруг вертикальной оси)
        };

        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // Left mouse button for rotate
                this.controls.isRotating = true;
            } else if (e.button === 1) { // Middle mouse button for pan
                this.controls.isDragging = true;
            }
            this.controls.lastX = e.clientX;
            this.controls.lastY = e.clientY;
        });

        this.canvas.addEventListener('mousemove', (e) => {
            const deltaX = e.clientX - this.controls.lastX;
            const deltaY = e.clientY - this.controls.lastY;

            if (this.controls.isDragging) {
                // Convert screen delta to world delta based on current zoom level
                const frustumWidth = this.camera.right - this.camera.left;
                const frustumHeight = this.camera.top - this.camera.bottom;

                const worldDeltaX = deltaX * (frustumWidth / this.canvas.clientWidth);
                const worldDeltaY = -deltaY * (frustumHeight / this.canvas.clientHeight); // Y is inverted

                // Move camera position
                this.camera.position.x -= worldDeltaX;
                this.camera.position.y -= worldDeltaY;

                // Update focus point accordingly
                this.focusPoint.x -= worldDeltaX;
                this.focusPoint.y -= worldDeltaY;

                // Update lookAt target to stay centered
                this.camera.lookAt(this.focusPoint);
            }
            else if (this.controls.isRotating) {
                // Rotate the camera around the focus point
                const rotationX = deltaY * this.controls.rotationSpeed;
                const rotationY = deltaX * this.controls.rotationSpeed;

                // Update rotation values
                this.controls.currentRotationX -= rotationX;
                this.controls.currentRotationY -= rotationY;

                // Limit vertical rotation to prevent flipping
                this.controls.currentRotationX = Math.max(-Math.PI/2, Math.min(Math.PI/2, this.controls.currentRotationX));

                // Calculate camera distance from focus point
                const offset = new THREE.Vector3();
                offset.subVectors(this.camera.position, this.focusPoint);
                const distance = offset.length();

                // Apply rotations
                const cosX = Math.cos(this.controls.currentRotationX);
                const sinX = Math.sin(this.controls.currentRotationX);
                const cosY = Math.cos(this.controls.currentRotationY);
                const sinY = Math.sin(this.controls.currentRotationY);

                // Calculate new camera position based on rotations
                const x = this.focusPoint.x + distance * sinY * cosX;
                const y = this.focusPoint.y + distance * sinX;
                const z = this.focusPoint.z + distance * cosY * cosX;

                this.camera.position.set(x, y, z);
                this.camera.lookAt(this.focusPoint);
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

        this.canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault(); // Prevent context menu on right click
        });

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();

            // Для ортографической камеры изменяем размер фрустума вместо перемещения камеры
            const zoomSpeed = 0.1;
            const wheelDelta = e.deltaY > 0 ? 1 + zoomSpeed : 1 - zoomSpeed;

            // Обновляем параметры камеры для масштабирования
            this.camera.left *= wheelDelta;
            this.camera.right *= wheelDelta;
            this.camera.top *= wheelDelta;
            this.camera.bottom *= wheelDelta;

            this.camera.updateProjectionMatrix();
        }, { passive: false });
    }

    updateMeshes(meshData) {
        // Сохраняем текущее состояние камеры
        const savedCameraState = {
            position: this.camera.position.clone(),
            rotationX: this.controls.currentRotationX,
            rotationY: this.controls.currentRotationY
        };

        // Clear old meshes
        this.meshes.forEach(item => {
            this.scene.remove(item.mesh);
            if (item.mesh.geometry) item.mesh.geometry.dispose();
            if (item.mesh.material) item.mesh.material.dispose();
        });
        this.meshes = [];

        if (!meshData || !meshData.meshes) {
            // Если новых данных нет, восстанавливаем камеру
            this.camera.position.copy(savedCameraState.position);
            this.focusPoint.set(0, 0, 0); // Установить точку фокуса в начало координат
            this.controls.currentRotationX = savedCameraState.rotationX;
            this.controls.currentRotationY = savedCameraState.rotationY;
            return;
        }

        // Create new meshes
        meshData.meshes.forEach((data, index) => {
            const geometry = new THREE.BufferGeometry();

            if (data.vertices && data.indices) {
                // Transform IFC coordinates to Three.js coordinates
                const transformedVertices = this.transformVerticesForThreeJS(data.vertices);
                
                geometry.setAttribute('position',
                    new THREE.BufferAttribute(new Float32Array(transformedVertices), 3));
                geometry.setIndex(
                    new THREE.BufferAttribute(new Uint32Array(data.indices), 1));
                geometry.computeVertexNormals();

                const color = data.color || 0x2563eb;
                const material = new THREE.MeshPhongMaterial({
                    color: color,
                    side: THREE.DoubleSide,
                    shininess: 30,
                    flatShading: true
                });

                const mesh = new THREE.Mesh(geometry, material);
                mesh.castShadow = true;
                mesh.receiveShadow = true;

                this.scene.add(mesh);

                this.meshes.push({
                    mesh: mesh,
                    id: data.id || `mesh_${index}`,
                    name: data.name || `Component ${index}`,
                    metadata: data.metadata || {}
                });
            }
        });

        // Проверяем, есть ли какие-либо меш-данные
        if (this.meshes.length > 0) {
            // Если были меш-данные, восстанавливаем камеру к предыдущему состоянию
            this.camera.position.copy(savedCameraState.position);
            this.focusPoint.set(0, 0, 0); // Установить точку фокуса в начало координат
            this.controls.currentRotationX = savedCameraState.rotationX;
            this.controls.currentRotationY = savedCameraState.rotationY;

            // Применяем вращение к камере
            this.applyCameraRotation();
        } else {
            // Если нет меш-данных, восстанавливаем камеру
            this.camera.position.copy(savedCameraState.position);
            this.focusPoint.set(0, 0, 0); // Установить точку фокуса в начало координат
            this.controls.currentRotationX = savedCameraState.rotationX;
            this.controls.currentRotationY = savedCameraState.rotationY;
        }
    }
    
    /**
     * Update meshes and focus camera on the new objects
     * @param {*} meshData 
     */
    updateMeshesAndFocus(meshData) {
        // Установить точку фокуса в начало координат перед обновлением
        this.focusPoint.set(0, 0, 0);
        this.updateMeshes(meshData);
        // Только после обновления мешей вызываем фокусировку
        if (this.meshes.length > 0) {
            this.frameAll();
        }
    }
    
    /**
     * Initialize camera focus on the first objects
     * @param {*} meshData 
     */
    initializeCameraFocus(meshData) {
        // При инициализации установить точку фокуса в начало координат
        this.focusPoint.set(0, 0, 0);
        this.updateMeshes(meshData);
        // При инициализации всегда фокусируемся на объекте
        if (this.meshes.length > 0) {
            this.frameAll();
        }
    }
    
    /**
     * Update meshes without changing camera orientation
     * @param {*} meshData 
     */
    updateMeshesPreserveView(meshData) {
        // Сохраняем текущее состояние камеры
        const savedCameraState = {
            position: this.camera.position.clone(),
            rotationX: this.controls.currentRotationX,
            rotationY: this.controls.currentRotationY
        };

        // Clear old meshes
        this.meshes.forEach(item => {
            this.scene.remove(item.mesh);
            if (item.mesh.geometry) item.mesh.geometry.dispose();
            if (item.mesh.material) item.mesh.material.dispose();
        });
        this.meshes = [];

        if (!meshData || !meshData.meshes) {
            // Если новых данных нет, восстанавливаем камеру
            this.camera.position.copy(savedCameraState.position);
            this.focusPoint.set(0, 0, 0); // Установить точку фокуса в начало координат
            this.controls.currentRotationX = savedCameraState.rotationX;
            this.controls.currentRotationY = savedCameraState.rotationY;
            return;
        }

        // Create new meshes
        meshData.meshes.forEach((data, index) => {
            const geometry = new THREE.BufferGeometry();

            if (data.vertices && data.indices) {
                // Transform IFC coordinates to Three.js coordinates
                const transformedVertices = this.transformVerticesForThreeJS(data.vertices);
                
                geometry.setAttribute('position',
                    new THREE.BufferAttribute(new Float32Array(transformedVertices), 3));
                geometry.setIndex(
                    new THREE.BufferAttribute(new Uint32Array(data.indices), 1));
                geometry.computeVertexNormals();

                const color = data.color || 0x2563eb;
                const material = new THREE.MeshPhongMaterial({
                    color: color,
                    side: THREE.DoubleSide,
                    shininess: 30,
                    flatShading: true
                });

                const mesh = new THREE.Mesh(geometry, material);
                mesh.castShadow = true;
                mesh.receiveShadow = true;

                this.scene.add(mesh);

                this.meshes.push({
                    mesh: mesh,
                    id: data.id || `mesh_${index}`,
                    name: data.name || `Component ${index}`,
                    metadata: data.metadata || {}
                });
            }
        });

        // Проверяем, есть ли какие-либо меш-данные
        if (this.meshes.length > 0) {
            // Если были меш-данные, восстанавливаем камеру к предыдущему состоянию
            this.camera.position.copy(savedCameraState.position);
            this.focusPoint.set(0, 0, 0); // Установить точку фокуса в начало координат
            this.controls.currentRotationX = savedCameraState.rotationX;
            this.controls.currentRotationY = savedCameraState.rotationY;

            // Применяем вращение к камере
            this.applyCameraRotation();
        } else {
            // Если нет меш-данных, восстанавливаем камеру
            this.camera.position.copy(savedCameraState.position);
            this.focusPoint.set(0, 0, 0); // Установить точку фокуса в начало координат
            this.controls.currentRotationX = savedCameraState.rotationX;
            this.controls.currentRotationY = savedCameraState.rotationY;
        }
    }

    /**
     * Transform vertices from IFC coordinate system to Three.js coordinate system
     * IFC typically uses Z-up coordinate system, while Three.js uses Y-up
     * This function transforms (x, y, z) to (x, z, -y) to align the systems
     * @param {Array<number>} vertices - Array of vertex coordinates [x1, y1, z1, x2, y2, z2, ...]
     * @returns {Array<number>} - Transformed array of vertex coordinates
     */
    transformVerticesForThreeJS(vertices) {
        const transformed = [];

        for (let i = 0; i < vertices.length; i += 3) {
            const x = vertices[i];
            const y = vertices[i + 1];
            const z = vertices[i + 2];

            // Transform from IFC (Z-up) to Three.js (Y-up)
            // Original: (x, y, z) where Z is up
            // Target: (x, y, z) where Y is up
            // So we map: (x, y, z) -> (x, z, -y) to account for different handedness
            transformed.push(x);
            transformed.push(z);
            transformed.push(-y);  // Negate to account for different handedness
        }

        return transformed;
    }

    /**
     * Get current camera rotation angles
     * @returns {{rotationX: number, rotationY: number}} Rotation angles in radians
     */
    getCameraRotation() {
        return {
            rotationX: this.controls.currentRotationX,
            rotationY: this.controls.currentRotationY
        };
    }

    /**
     * Set camera rotation angles
     * @param {number} rotationX - Rotation around X-axis in radians
     * @param {number} rotationY - Rotation around Y-axis in radians
     */
    setCameraRotation(rotationX, rotationY) {
        this.controls.currentRotationX = rotationX;
        this.controls.currentRotationY = rotationY;

        // Calculate camera distance from target
        const offset = new THREE.Vector3();
        offset.subVectors(this.camera.position, this.controls.targetPosition);
        const distance = offset.length();
        
        // Apply rotations
        const cosX = Math.cos(this.controls.currentRotationX);
        const sinX = Math.sin(this.controls.currentRotationX);
        const cosY = Math.cos(this.controls.currentRotationY);
        const sinY = Math.sin(this.controls.currentRotationY);
        
        // Calculate new camera position based on rotations
        const x = this.controls.targetPosition.x + distance * sinY * cosX;
        const y = this.controls.targetPosition.y + distance * sinX;
        const z = this.controls.targetPosition.z + distance * cosY * cosX;
        
        this.camera.position.set(x, y, z);
        this.camera.lookAt(this.controls.targetPosition);
    }

    onCanvasClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);

        const intersects = this.raycaster.intersectObjects(
            this.meshes.map(item => item.mesh)
        );

        if (intersects.length > 0) {
            const clicked = intersects[0].object;
            const meshItem = this.meshes.find(item => item.mesh === clicked);

            if (meshItem) {
                this.selectMesh(meshItem);
                // Установить точку фокуса на центр геометрии выбранного элемента
                const geometry = clicked.geometry;
                const boundingBox = new THREE.Box3().setFromObject(clicked);
                const center = new THREE.Vector3();
                boundingBox.getCenter(center);
                this.focusPoint.copy(center);
                window.dispatchEvent(new CustomEvent('meshSelected', {
                    detail: meshItem
                }));
            }
        } else {
            this.deselectMesh();
            // При отмене выбора вернуть точку фокуса к началу координат
            this.focusPoint.set(0, 0, 0);
        }
    }

    selectMesh(meshItem) {
        this.deselectMesh();

        this.selectedMesh = meshItem;
        meshItem.mesh.material.emissive.setHex(0xffff00);
        meshItem.mesh.material.emissiveIntensity = 0.3;
        
        // Установить точку фокуса на центр геометрии выбранного элемента
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
            
            // При отмене выбора вернуть точку фокуса к началу координат
            this.focusPoint.set(0, 0, 0);
        }
    }

    frameAll() {
        if (this.meshes.length === 0) return;

        const box = new THREE.Box3();
        this.meshes.forEach(item => {
            box.expandByObject(item.mesh);
        });

        const center = box.getCenter(new THREE.Vector3());

        // Сохраняем текущие углы вращения
        const savedRotationX = this.controls.currentRotationX;
        const savedRotationY = this.controls.currentRotationY;

        // Вычисляем расстояние от камеры до центра объектов
        const offset = new THREE.Vector3();
        offset.subVectors(this.camera.position, this.focusPoint);
        const prevDistance = offset.length();

        // Устанавливаем позицию камеры на центр объекта
        this.camera.position.x = center.x;
        this.camera.position.y = center.y;
        this.camera.position.z = center.z + (prevDistance || 1000); // сохраняем расстояние до цели
        this.camera.lookAt(center.x, center.y, center.z);

        // Обновляем точку фокуса на центр объектов
        this.focusPoint.copy(center);

        // Восстанавливаем сохраненные углы вращения (не сбрасываем их)
        this.controls.currentRotationX = savedRotationX;
        this.controls.currentRotationY = savedRotationY;

        // Рассчитываем размеры для охвата всех объектов
        const size = box.getSize(new THREE.Vector3());
        const maxSize = Math.max(size.x, size.y) * 0.8; // добавляем небольшой отступ

        // Обновляем параметры ортографической камеры
        const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        const frustumSize = Math.max(maxSize, 200); // минимальный размер фрустума

        this.camera.left = -frustumSize * aspect;
        this.camera.right = frustumSize * aspect;
        this.camera.top = frustumSize;
        this.camera.bottom = -frustumSize;

        this.camera.updateProjectionMatrix();

        // Применяем вращение к камере
        this.applyCameraRotation();

        // Сбрасываем флаг первого запуска
        this.firstRun = false;
    }

    /**
     * Apply current rotation to camera position
     */
    applyCameraRotation() {
        // Calculate camera distance from focus point
        const offset = new THREE.Vector3();
        offset.subVectors(this.camera.position, this.focusPoint);
        const distance = offset.length();

        // Apply rotations
        const cosX = Math.cos(this.controls.currentRotationX);
        const sinX = Math.sin(this.controls.currentRotationX);
        const cosY = Math.cos(this.controls.currentRotationY);
        const sinY = Math.sin(this.controls.currentRotationY);

        // Calculate new camera position based on rotations
        const x = this.focusPoint.x + distance * sinY * cosX;
        const y = this.focusPoint.y + distance * sinX;
        const z = this.focusPoint.z + distance * cosY * cosX;

        this.camera.position.set(x, y, z);
        this.camera.lookAt(this.focusPoint);
    }

    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        // Обновляем соотношение сторон для ортографической камеры
        const aspect = width / height;
        const frustumSize = (this.camera.right - this.camera.left) / 2; // сохраняем текущий размер фрустума
        
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

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IFCViewer;
}
