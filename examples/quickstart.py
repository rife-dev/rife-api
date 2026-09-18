        """Minimal RIFE example: create one prediction and print the output URL(s)."""
        import rife_api

        output = rife_api.run({
    "image_url": "https://example.com/input.png"
})
        print(output)
