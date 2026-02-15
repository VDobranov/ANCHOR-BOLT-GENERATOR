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

        this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 10000);
        this.camera.position.set(500, 400, 600);
        this.camera.lookAt(0, 0, 400);

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
        // Simple orbit camera controls
        this.controls = {
            isRotating: false,
            lastX: 0,
            lastY: 0,
            rotationSpeed: 0.005,
            zoomSpeed: 50
        };

        this.canvas.addEventListener('mousedown', (e) => {
            this.controls.isRotating = true;
            this.controls.lastX = e.clientX;
            this.controls.lastY = e.clientY;
        });

        this.canvas.addEventListener('mousemove', (e) => {
            if (this.controls.isRotating) {
                const deltaX = e.clientX - this.controls.lastX;
                const deltaY = e.clientY - this.controls.lastY;

                const position = this.camera.position;
                const radius = position.length();

                const theta = Math.atan2(position.x, position.z);
                const phi = Math.acos(position.y / radius);

                const newTheta = theta - deltaX * this.controls.rotationSpeed;
                const newPhi = Math.max(0.1, Math.min(Math.PI - 0.1, phi + deltaY * this.controls.rotationSpeed));

                this.camera.position.x = radius * Math.sin(newPhi) * Math.sin(newTheta);
                this.camera.position.y = radius * Math.cos(newPhi);
                this.camera.position.z = radius * Math.sin(newPhi) * Math.cos(newTheta);
                this.camera.lookAt(0, 0, 400);

                this.controls.lastX = e.clientX;
                this.controls.lastY = e.clientY;
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            this.controls.isRotating = false;
        });

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const position = this.camera.position;
            const radius = position.length();
            const newRadius = Math.max(100, Math.min(5000, radius + e.deltaY * 0.5));

            const direction = position.normalize();
            this.camera.position.copy(direction.multiplyScalar(newRadius));
            this.camera.lookAt(0, 0, 400);
        }, { passive: false });
    }

    updateMeshes(meshData) {
        // Clear old meshes
        this.meshes.forEach(item => {
            this.scene.remove(item.mesh);
            if (item.mesh.geometry) item.mesh.geometry.dispose();
            if (item.mesh.material) item.mesh.material.dispose();
        });
        this.meshes = [];

        if (!meshData || !meshData.meshes) return;

        // Create new meshes
        meshData.meshes.forEach((data, index) => {
            const geometry = new THREE.BufferGeometry();

            if (data.vertices && data.indices) {
                geometry.setAttribute('position',
                    new THREE.BufferAttribute(new Float32Array(data.vertices), 3));
                geometry.setIndex(
                    new THREE.BufferAttribute(new Uint32Array(data.indices), 1));
                geometry.computeVertexNormals();

                const color = data.color || 0x2563eb;
                const material = new THREE.MeshPhongMaterial({
                    color: color,
                    side: THREE.DoubleSide,
                    shininess: 30
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

        this.frameAll();
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
                window.dispatchEvent(new CustomEvent('meshSelected', {
                    detail: meshItem
                }));
            }
        } else {
            this.deselectMesh();
        }
    }

    selectMesh(meshItem) {
        this.deselectMesh();

        this.selectedMesh = meshItem;
        meshItem.mesh.material.emissive.setHex(0xffff00);
        meshItem.mesh.material.emissiveIntensity = 0.3;
    }

    deselectMesh() {
        if (this.selectedMesh) {
            this.selectedMesh.mesh.material.emissive.setHex(0x000000);
            this.selectedMesh.mesh.material.emissiveIntensity = 0;
            this.selectedMesh = null;
        }
    }

    frameAll() {
        if (this.meshes.length === 0) return;

        const box = new THREE.Box3();
        this.meshes.forEach(item => {
            box.expandByObject(item.mesh);
        });

        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = this.camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));

        cameraZ *= 1.5;

        this.camera.position.z = center.z + cameraZ;
        this.camera.position.x = center.x + cameraZ * 0.3;
        this.camera.position.y = center.y + cameraZ * 0.3;
        this.camera.lookAt(center);
    }

    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        this.camera.aspect = width / height;
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
