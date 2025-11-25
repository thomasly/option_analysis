"""
数据加载器模块，支持AlexNet训练和测试数据
"""

import torch
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class CustomDataset(Dataset):
    """
    自定义数据集类，支持16x16图像数据
    """

    def __init__(
        self,
        data: np.ndarray,
        labels: np.ndarray,
        transform: Optional[transforms.Compose] = None,
    ):
        """
        初始化数据集

        Args:
            data: 图像数据，形状为 (N, H, W) 或 (N, C, H, W)
            labels: 标签数据，形状为 (N,)
            transform: 数据变换
        """
        self.data = data
        self.labels = labels
        self.transform = transform

        # 确保数据格式正确
        if len(self.data.shape) == 3:
            # 如果是 (N, H, W)，添加通道维度
            self.data = self.data.reshape(
                self.data.shape[0], 1, self.data.shape[1], self.data.shape[2]
            )

        logger.info(
            f"数据集初始化: {len(self.data)} 个样本, 标签范围: {np.min(labels)}-{np.max(labels)}"
        )

    def __len__(self) -> int:
        """返回数据集大小"""
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """
        获取单个样本

        Args:
            idx: 样本索引

        Returns:
            (图像张量, 标签)
        """
        image = self.data[idx]
        label = int(self.labels[idx])

        # 转换为torch张量
        if not isinstance(image, torch.Tensor):
            image = torch.from_numpy(image).float()

        # 应用变换
        if self.transform:
            image = self.transform(image)

        return image, label


class DataLoaderManager:
    """
    数据加载器管理器，负责创建和管理训练、验证、测试数据加载器
    """

    def __init__(
        self,
        batch_size: int = 32,
        train_split: float = 0.8,
        val_split: float = 0.1,
        test_split: float = 0.1,
        random_seed: int = 42,
    ):
        """
        初始化数据加载器管理器

        Args:
            batch_size: 批次大小
            train_split: 训练集比例
            val_split: 验证集比例
            test_split: 测试集比例
            random_seed: 随机种子
        """
        self.batch_size = batch_size
        self.train_split = train_split
        self.val_split = val_split
        self.test_split = test_split
        self.random_seed = random_seed

        # 设置随机种子
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)

        # 数据变换
        self.train_transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=10),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5]),  # 归一化到[-1, 1]
            ]
        )

        self.val_transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5]),
            ]
        )

        logger.info("数据加载器管理器初始化完成")

    def create_dataloaders(
        self, data: np.ndarray, labels: np.ndarray, shuffle_train: bool = True
    ) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        创建训练、验证、测试数据加载器

        Args:
            data: 图像数据
            labels: 标签数据
            shuffle_train: 是否打乱训练数据

        Returns:
            (训练数据加载器, 验证数据加载器, 测试数据加载器)
        """
        try:
            # 创建完整数据集
            full_dataset = CustomDataset(data, labels, self.val_transform)

            # 计算分割大小
            total_size = len(full_dataset)
            train_size = int(self.train_split * total_size)
            val_size = int(self.val_split * total_size)
            test_size = total_size - train_size - val_size

            logger.info(
                f"数据分割: 训练集={train_size}, 验证集={val_size}, 测试集={test_size}"
            )

            # 分割数据集
            train_dataset, val_dataset, test_dataset = random_split(
                full_dataset,
                [train_size, val_size, test_size],
                generator=torch.Generator().manual_seed(self.random_seed),
            )

            # 为训练集应用数据增强
            train_dataset.dataset.transform = self.train_transform

            # 创建数据加载器
            train_loader = DataLoader(
                train_dataset,
                batch_size=self.batch_size,
                shuffle=shuffle_train,
                num_workers=2,
                pin_memory=True,
            )

            val_loader = DataLoader(
                val_dataset,
                batch_size=self.batch_size,
                shuffle=False,
                num_workers=2,
                pin_memory=True,
            )

            test_loader = DataLoader(
                test_dataset,
                batch_size=self.batch_size,
                shuffle=False,
                num_workers=2,
                pin_memory=True,
            )

            logger.info("数据加载器创建完成")
            return train_loader, val_loader, test_loader

        except Exception as e:
            logger.error(f"创建数据加载器失败: {e}")
            raise

    def create_single_dataloader(
        self,
        data: np.ndarray,
        labels: np.ndarray,
        shuffle: bool = False,
        use_augmentation: bool = False,
    ) -> DataLoader:
        """
        创建单个数据加载器

        Args:
            data: 图像数据
            labels: 标签数据
            shuffle: 是否打乱数据
            use_augmentation: 是否使用数据增强

        Returns:
            数据加载器
        """
        transform = self.train_transform if use_augmentation else self.val_transform
        dataset = CustomDataset(data, labels, transform)

        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle,
            num_workers=2,
            pin_memory=True,
        )


def generate_synthetic_data(
    num_samples: int = 1000,
    num_classes: int = 10,
    image_size: int = 16,
    channels: int = 1,
    noise_level: float = 0.1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成合成数据用于测试

    Args:
        num_samples: 样本数量
        num_classes: 类别数量
        image_size: 图像尺寸
        channels: 通道数
        noise_level: 噪声水平

    Returns:
        (图像数据, 标签数据)
    """
    logger.info(f"生成合成数据: {num_samples} 个样本, {num_classes} 个类别")

    # 生成标签
    labels = np.random.randint(0, num_classes, num_samples)

    # 生成图像数据
    images = np.zeros((num_samples, channels, image_size, image_size))

    for i in range(num_samples):
        label = labels[i]

        # 为每个类别创建不同的模式
        if label == 0:  # 圆形
            center = image_size // 2
            y, x = np.ogrid[:image_size, :image_size]
            mask = (x - center) ** 2 + (y - center) ** 2 <= (image_size // 3) ** 2
            images[i, 0] = mask.astype(float)
        elif label == 1:  # 矩形
            start = image_size // 4
            end = 3 * image_size // 4
            images[i, 0, start:end, start:end] = 1.0
        elif label == 2:  # 对角线
            for j in range(image_size):
                if j < image_size:
                    images[i, 0, j, j] = 1.0
        elif label == 3:  # 反对角线
            for j in range(image_size):
                if j < image_size:
                    images[i, 0, j, image_size - 1 - j] = 1.0
        else:  # 随机模式
            images[i, 0] = np.random.rand(image_size, image_size)

        # 添加噪声
        noise = np.random.normal(0, noise_level, (image_size, image_size))
        images[i, 0] += noise

    # 归一化到[0, 1]
    images = np.clip(images, 0, 1)

    logger.info(f"合成数据生成完成: 图像形状={images.shape}, 标签形状={labels.shape}")
    return images, labels


def load_data_from_files(
    data_dir: str, data_file: str = "data.npy", labels_file: str = "labels.npy"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    从文件加载数据

    Args:
        data_dir: 数据目录
        data_file: 数据文件名
        labels_file: 标签文件名

    Returns:
        (图像数据, 标签数据)
    """
    try:
        data_path = os.path.join(data_dir, data_file)
        labels_path = os.path.join(data_dir, labels_file)

        if not os.path.exists(data_path) or not os.path.exists(labels_path):
            logger.warning(f"数据文件不存在，将生成合成数据")
            return generate_synthetic_data()

        data = np.load(data_path)
        labels = np.load(labels_path)

        logger.info(f"从文件加载数据: 图像形状={data.shape}, 标签形状={labels.shape}")
        return data, labels

    except Exception as e:
        logger.error(f"加载数据失败: {e}")
        logger.info("将生成合成数据作为替代")
        return generate_synthetic_data()


if __name__ == "__main__":
    # 测试数据加载器
    print("测试数据加载器...")

    # 生成测试数据
    data, labels = generate_synthetic_data(num_samples=100, num_classes=5)

    # 创建数据加载器管理器
    manager = DataLoaderManager(batch_size=16)

    # 创建数据加载器
    train_loader, val_loader, test_loader = manager.create_dataloaders(data, labels)

    print(f"训练集批次数: {len(train_loader)}")
    print(f"验证集批次数: {len(val_loader)}")
    print(f"测试集批次数: {len(test_loader)}")

    # 测试一个批次
    for batch_data, batch_labels in train_loader:
        print(f"批次数据形状: {batch_data.shape}")
        print(f"批次标签形状: {batch_labels.shape}")
        print(f"标签值: {batch_labels}")
        break


