# GitHub Setup Guide for Helm Aware

This guide explains how to set up the necessary GitHub tokens and permissions for the Helm Aware application to build and push Docker images to GitHub Container Registry (GHCR).

## 🔐 Required Permissions

The application needs the following permissions to work properly:

1. **Read repository contents** - To access the source code
2. **Write packages** - To push Docker images to GHCR
3. **Read and write workflow permissions** - To run GitHub Actions

## 🎫 Token Types

### Option 1: GITHUB_TOKEN (Recommended - Automatic)

The `GITHUB_TOKEN` is automatically provided by GitHub Actions and is the **recommended approach** for most use cases.

**Advantages:**
- ✅ Automatically created and managed by GitHub
- ✅ No manual token setup required
- ✅ Automatically rotated for security
- ✅ Minimal permissions (principle of least privilege)

**Setup:**
1. Go to your repository settings
2. Navigate to **Settings** → **Actions** → **General**
3. Under **Workflow permissions**, select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Save the changes

### Option 2: Personal Access Token (PAT) - Advanced

Use a Personal Access Token if you need more granular control or are hitting rate limits.

**When to use:**
- You need to push to multiple repositories
- You're hitting GitHub API rate limits
- You need custom permissions

**Setup:**
1. Go to **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token** → **Generate new token (classic)**
3. Configure the token:
   - **Note**: `helm-aware-ghcr-token`
   - **Expiration**: Choose appropriate expiration (90 days recommended)
   - **Scopes**:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `write:packages` (Upload packages to GitHub Package Registry)
     - ✅ `read:packages` (Download packages from GitHub Package Registry)
4. Click **Generate token**
5. **Copy the token immediately** (you won't see it again)

**Add to repository secrets:**
1. Go to your repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `GHCR_TOKEN`
4. Value: Paste your personal access token
5. Click **Add secret**

## 🔧 Workflow Configuration

The GitHub Actions workflow is already configured to use the appropriate token:

```yaml
- name: Log in to Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}  # Uses automatic token
```

If using a PAT, change the password line to:
```yaml
password: ${{ secrets.GHCR_TOKEN }}  # Uses custom PAT
```

## 🚀 Testing the Setup

### 1. Manual Trigger
1. Go to your repository → **Actions** tab
2. Select **Build and Push Docker Image**
3. Click **Run workflow**
4. Choose branch and optionally add a custom tag
5. Click **Run workflow**

### 2. Automatic Trigger
1. Make changes to files in the `app/` directory
2. Commit and push to `main` or `master` branch
3. The workflow will automatically trigger

### 3. Verify Success
1. Check the **Actions** tab for workflow status
2. Go to **Packages** tab to see your Docker image
3. The image will be available at: `ghcr.io/YOUR_USERNAME/helm-aware:latest`

## 📦 Image Naming Convention

The workflow creates images with the following naming pattern:

- **Latest**: `ghcr.io/YOUR_USERNAME/helm-aware:latest`
- **Branch**: `ghcr.io/YOUR_USERNAME/helm-aware:main`
- **Commit**: `ghcr.io/YOUR_USERNAME/helm-aware:main-SHA`
- **Custom**: `ghcr.io/YOUR_USERNAME/helm-aware:CUSTOM_TAG`

## 🔍 Troubleshooting

### Common Issues

#### 1. "Permission denied" error
**Solution**: Ensure workflow has write permissions
- Go to **Settings** → **Actions** → **General**
- Enable **Read and write permissions**

#### 2. "Authentication failed" error
**Solution**: Check token configuration
- Verify `GITHUB_TOKEN` is available (automatic)
- Or ensure `GHCR_TOKEN` secret is properly set

#### 3. "Package not found" error
**Solution**: Check package visibility
- Go to **Packages** tab
- Ensure package is visible to your deployment

#### 4. Rate limiting
**Solution**: Use Personal Access Token
- Create PAT with appropriate scopes
- Update workflow to use `GHCR_TOKEN`

### Debug Steps

1. **Check workflow logs** in the Actions tab
2. **Verify repository permissions** in Settings
3. **Test token manually** using Docker CLI:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

## 🔒 Security Best Practices

1. **Use GITHUB_TOKEN when possible** - It's automatically managed
2. **Set appropriate expiration** for PATs (90 days max)
3. **Use minimal required scopes** for PATs
4. **Rotate tokens regularly** if using PATs
5. **Monitor package access** in repository settings

## 📋 Quick Setup Checklist

- [ ] Repository has Actions enabled
- [ ] Workflow permissions set to "Read and write"
- [ ] GITHUB_TOKEN is available (automatic)
- [ ] Or GHCR_TOKEN secret is configured (if using PAT)
- [ ] Test workflow with manual trigger
- [ ] Verify image appears in Packages tab
- [ ] Update Kubernetes deployment to use new image

## 🎯 Next Steps

After successful setup:

1. **Deploy to Kubernetes** using the new image
2. **Monitor the application** for any issues
3. **Set up automated deployments** if needed
4. **Configure image scanning** for security

For more information, see:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Token Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication) 