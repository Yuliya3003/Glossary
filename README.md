# ЗАПУСК
### Сборка образа
```bash
docker build -t glossary_app .
```
### Запуск контейнера
```bash
docker run -d --name mycontainer -p 80:80 glossary_app
```
### После запуска контейнера документация будет доступна по адресу
http://127.0.0.1/docs

## Глоссарий для хранения определений
1. Можно добавлять термины
  ![Снимок экрана 2024-12-22 153215](https://github.com/user-attachments/assets/4ef8d888-831b-4d93-a5c2-4ffcc15908a8)
3. Можно редактировать термины
   ![Снимок экрана 2024-12-22 153323](https://github.com/user-attachments/assets/83d2131d-fd47-4540-9893-a6f59e68f4b7)
5. Можно удалять термины
   ![Снимок экрана 2024-12-22 153258](https://github.com/user-attachments/assets/20f64e44-c4e6-41a0-ad68-3697824a3d08)
7. Можно искать термин по названию
   ![Снимок экрана 2024-12-22 153335](https://github.com/user-attachments/assets/9dc8f8aa-7fcc-49c5-99b0-761ab11612e1)
9. Можно просматривать все термины
    ![Снимок экрана 2024-12-22 153201](https://github.com/user-attachments/assets/4da8437c-0172-4be4-8f7e-f09331c0f670)
