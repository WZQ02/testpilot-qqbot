import asyncio
from aiohttp import web
import threading
import os
from pathlib import Path
import mimetypes

class AdvancedStaticServer:
    def __init__(self, host='localhost', port=8104, root_dir='.'):
        self.host = host
        self.port = port
        self.root_dir = Path(root_dir).resolve()
        self.app = web.Application()
        self.setup_routes()
        self.runner = None
        self.site = None
        self.thread = None
        self._stop_event = threading.Event()

    def setup_routes(self):
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/{path:.*}', self.handle_static)
        # self.app.router.add_post('/api/upload', self.handle_upload)

    async def handle_index(self, request):
        """处理根路径，返回 index.html"""
        index_file = self.root_dir / 'index.html'
        if index_file.exists():
            return web.FileResponse(index_file)
        else:
            return web.Response(text="Index file not found", status=404)

    async def handle_static(self, request):
        """处理静态文件请求"""
        path = request.match_info['path']
        file_path = self.root_dir / path
        
        # 安全检查：确保文件在根目录内
        try:
            file_path.resolve().relative_to(self.root_dir)
        except (ValueError, RuntimeError):
            return web.Response(text="Forbidden", status=403)
        
        if file_path.is_file():
            # 设置正确的 MIME 类型
            mime_type, _ = mimetypes.guess_type(str(file_path))
            response = web.FileResponse(file_path)
            if mime_type:
                response.headers['Content-Type'] = mime_type
            return response
        else:
            return web.Response(text="File not found", status=404)
    """
    async def handle_upload(self, request):
        # 文件上传示例
        data = await request.post()
        if 'file' in data:
            file_field = data['file']
            filename = file_field.filename
            file_path = self.root_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_field.file.read())
            
            return web.json_response({
                'status': 'success',
                'filename': filename,
                'size': os.path.getsize(file_path)
            })
        
        return web.json_response({'status': 'error', 'message': 'No file provided'}, status=400)
    """

    async def start_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        print(f"testpilot web服务器已启动于： http://{self.host}:{self.port}")
        print(f"web根目录： {self.root_dir}")

    async def stop_server(self):
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

    def _run_in_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.start_server())
            
            # 保持运行
            async def keep_alive():
                while not self._stop_event.is_set():
                    await asyncio.sleep(0.1)
            
            loop.run_until_complete(keep_alive())
        finally:
            loop.run_until_complete(self.stop_server())
            loop.close()

    def start(self):
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self.thread.start()
        return self.thread

    def stop(self):
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

web_directory = './web'  # 修改为你的实际目录

    # 启动服务器
server = AdvancedStaticServer(port=8104, root_dir=web_directory)
server.start()

""" 
try:
    import time
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    server.stop()
"""