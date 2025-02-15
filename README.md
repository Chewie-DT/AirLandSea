# Air, Land & Sea - Online Multiplayer Game

## Description
This is a web-based implementation of the board game *Air, Land & Sea*, featuring:
- Multiplayer gameplay
- Real-time WebSockets
- FastAPI backend
- React frontend
- CI/CD deployment on Oracle Cloud

## Project Structure
```
├── backend
│   ├── app
│   ├── requirements.txt
│   └── server.py
├── frontend
│   ├── public
│   ├── src
│   ├── package.json
│   └── tailwind.config.js
├── .github
│   └── workflows
│       ├── backend-deploy.yml
│       └── frontend-deploy.yml
├── .gitignore
└── README.md
```

## Installation

### Backend
1. Navigate to the `backend` directory:
   ```sh
   cd backend
   ```
2. Create a virtual environment:
   ```sh
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```sh
   source venv/bin/activate
   ```
4. Install the dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Run the server:
   ```sh
   uvicorn server:app --reload
   ```

### Frontend
1. Navigate to the `frontend` directory:
   ```sh
   cd frontend
   ```
2. Install the dependencies:
   ```sh
   npm install
   ```
3. Start the development server:
   ```sh
   npm start
   ```

## Usage
Once both the backend and frontend servers are running, open your browser and navigate to `http://localhost:3000` to start playing the game.

## Deployment
The project is set up for CI/CD deployment on Oracle Cloud. Ensure that the appropriate secrets are configured in the repository settings for seamless deployment.

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
