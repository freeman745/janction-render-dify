from dify_plugin import DifyPluginEnv, Plugin

# HTTPX_TIMEOUT: how long reading a file the user gave to a tool may take (scenes can be up to 100 MB).
plugin = Plugin(DifyPluginEnv(HTTPX_TIMEOUT=180))

if __name__ == "__main__":
    plugin.run()
