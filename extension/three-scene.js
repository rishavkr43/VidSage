// three-scene.js - Three.js animated background
class ThreeScene {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.particles = null;
        this.animationId = null;
        
        this.init();
        this.animate();
    }
    
    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        
        // Camera setup
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.z = 5;
        
        // Renderer setup
        const canvas = document.getElementById('three-canvas');
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: canvas, 
            alpha: true, 
            antialias: true 
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Create particle system
        this.createParticles();
        
        // Create floating geometric shapes
        this.createGeometry();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    createParticles() {
        const particlesGeometry = new THREE.BufferGeometry();
        const particlesCount = 1000;
        
        const positions = new Float32Array(particlesCount * 3);
        const colors = new Float32Array(particlesCount * 3);
        
        for (let i = 0; i < particlesCount * 3; i += 3) {
            // Positions
            positions[i] = (Math.random() - 0.5) * 20;
            positions[i + 1] = (Math.random() - 0.5) * 20;
            positions[i + 2] = (Math.random() - 0.5) * 20;
            
            // Colors - gradient from purple to blue
            const colorIntensity = Math.random();
            colors[i] = 0.4 + colorIntensity * 0.4;     // R
            colors[i + 1] = 0.5 + colorIntensity * 0.4; // G
            colors[i + 2] = 0.8 + colorIntensity * 0.2; // B
        }
        
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        
        const particlesMaterial = new THREE.PointsMaterial({
            size: 0.02,
            vertexColors: true,
            blending: THREE.AdditiveBlending,
            transparent: true,
            opacity: 0.8
        });
        
        this.particles = new THREE.Points(particlesGeometry, particlesMaterial);
        this.scene.add(this.particles);
    }
    
    createGeometry() {
        // Create floating geometric shapes
        const shapes = [];
        const geometries = [
            new THREE.BoxGeometry(0.2, 0.2, 0.2),
            new THREE.SphereGeometry(0.1, 16, 16),
            new THREE.ConeGeometry(0.1, 0.3, 8),
            new THREE.TetrahedronGeometry(0.15)
        ];
        
        const materials = [
            new THREE.MeshBasicMaterial({ 
                color: 0x667eea, 
                transparent: true, 
                opacity: 0.3,
                wireframe: true 
            }),
            new THREE.MeshBasicMaterial({ 
                color: 0x764ba2, 
                transparent: true, 
                opacity: 0.3,
                wireframe: true 
            }),
            new THREE.MeshBasicMaterial({ 
                color: 0x9c88ff, 
                transparent: true, 
                opacity: 0.3,
                wireframe: true 
            })
        ];
        
        // Create multiple shapes
        for (let i = 0; i < 15; i++) {
            const geometry = geometries[Math.floor(Math.random() * geometries.length)];
            const material = materials[Math.floor(Math.random() * materials.length)];
            const mesh = new THREE.Mesh(geometry, material);
            
            // Random position
            mesh.position.set(
                (Math.random() - 0.5) * 10,
                (Math.random() - 0.5) * 10,
                (Math.random() - 0.5) * 10
            );
            
            // Random rotation
            mesh.rotation.set(
                Math.random() * Math.PI,
                Math.random() * Math.PI,
                Math.random() * Math.PI
            );
            
            // Store initial position and random speed
            mesh.userData = {
                initialY: mesh.position.y,
                speed: Math.random() * 0.02 + 0.01,
                rotationSpeed: {
                    x: (Math.random() - 0.5) * 0.02,
                    y: (Math.random() - 0.5) * 0.02,
                    z: (Math.random() - 0.5) * 0.02
                }
            };
            
            shapes.push(mesh);
            this.scene.add(mesh);
        }
        
        this.shapes = shapes;
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        const time = Date.now() * 0.001;
        
        // Animate particles
        if (this.particles) {
            this.particles.rotation.x = time * 0.1;
            this.particles.rotation.y = time * 0.05;
        }
        
        // Animate geometric shapes
        if (this.shapes) {
            this.shapes.forEach((shape, index) => {
                // Floating animation
                shape.position.y = shape.userData.initialY + Math.sin(time * shape.userData.speed + index) * 0.5;
                
                // Rotation animation
                shape.rotation.x += shape.userData.rotationSpeed.x;
                shape.rotation.y += shape.userData.rotationSpeed.y;
                shape.rotation.z += shape.userData.rotationSpeed.z;
            });
        }
        
        // Camera gentle movement
        this.camera.position.x = Math.sin(time * 0.1) * 0.5;
        this.camera.position.y = Math.cos(time * 0.15) * 0.3;
        this.camera.lookAt(this.scene.position);
        
        this.renderer.render(this.scene, this.camera);
    }
    
    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        window.removeEventListener('resize', this.onWindowResize);
    }
}

// Initialize the Three.js scene when the page loads
let threeScene;

document.addEventListener('DOMContentLoaded', () => {
    threeScene = new ThreeScene();
});

// Clean up when page unloads
window.addEventListener('beforeunload', () => {
    if (threeScene) {
        threeScene.destroy();
    }
});